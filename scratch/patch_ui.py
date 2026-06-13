with open('templates/ticker.html', 'r') as f:
    content = f.read()

old_chart = """                                    backgroundColor: isPct ? 'rgba(31, 77, 31, 0.1)' : '#1f4d1f',
                                    borderColor: '#1f4d1f',
                                    borderWidth: 2,
                                    fill: isPct,
                                    tension: 0.1,
                                    pointBackgroundColor: '#1f4d1f',"""

new_chart = """                                    backgroundColor: isPct ? 'rgba(0, 51, 102, 0.1)' : '#003366',
                                    borderColor: '#003366',
                                    borderWidth: 2,
                                    fill: isPct,
                                    tension: 0.1,
                                    pointBackgroundColor: '#003366',"""

content = content.replace(old_chart, new_chart)

with open('templates/ticker.html', 'w') as f:
    f.write(content)

with open('app.py', 'r') as f:
    app_content = f.read()

old_indices = """INDEX_SYMBOLS = ["^GSPC", "^RUA", "^IXIC", "^DJI"]
INDEX_NAMES = {
    "^GSPC": "S&P 500",
    "^RUA": "Russell 3000",
    "^IXIC": "Nasdaq",
    "^DJI": "Dow Jones"
}"""

new_indices = """INDEX_SYMBOLS = ["^GSPC", "^IXIC", "^N225", "^OMX"]
INDEX_NAMES = {
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq",
    "^N225": "Nikkei 225",
    "^OMX": "OMX Stockholm 30"
}"""

app_content = app_content.replace(old_indices, new_indices)

with open('app.py', 'w') as f:
    f.write(app_content)

with open('templates/index.html', 'r') as f:
    index_content = f.read()

index_content = index_content.replace('<div class="box-header">US MARKET INDICES</div>', '<div class="box-header">MARKET INDICES</div>')

old_link = """<a href="{{ url_for('index_constituents', index_id='sp500' if index.symbol=='^GSPC' else ('nasdaq100' if index.symbol=='^IXIC' else ('dow30' if index.symbol=='^DJI' else 'russell3000'))) }}">{{ index.name }}</a>"""
new_link = """<a href="{{ url_for('index_constituents', index_id='sp500' if index.symbol=='^GSPC' else ('nasdaq100' if index.symbol=='^IXIC' else ('nikkei225' if index.symbol=='^N225' else 'omxs30'))) }}">{{ index.name }}</a>"""

index_content = index_content.replace(old_link, new_link)

with open('templates/index.html', 'w') as f:
    f.write(index_content)

print('Patched files successfully!')
