with open('app.py', 'r') as f:
    content = f.read()

old_app = """    formatted_constituents = []
    for stock in constituents:
        market_cap = stock.get('market_cap')
        pe_ratio = stock.get('pe_ratio')"""

new_app = """    index_ticker_map = {
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
        pe_ratio = stock.get('pe_ratio')"""

content = content.replace(old_app, new_app)

old_app_ret = """    return render_template('constituents.html', 
                           index_id=index_id, 
                           index_name=index_name,
                           constituents=formatted_constituents,"""

new_app_ret = """    return render_template('constituents.html', 
                           index_id=index_id, 
                           index_name=index_name,
                           index_quote=index_quote,
                           constituents=formatted_constituents,"""

content = content.replace(old_app_ret, new_app_ret)

with open('app.py', 'w') as f:
    f.write(content)

with open('templates/constituents.html', 'r') as f:
    html_content = f.read()

old_html = """            <div class="box-header">INDEX {{ index_name|upper }} CONSTITUENTS</div>"""

new_html = """            <div class="box-header">
                INDEX {{ index_name|upper }} CONSTITUENTS
                {% if index_quote %}
                <span style="float: right; font-weight: normal; font-size: 11px;">
                    Daily Performance: 
                    <span class="text-bold" style="font-family: 'Courier New', monospace;">{{ "{:,.2f}".format(index_quote.price) }}</span>
                    <span class="{% if index_quote.change >= 0 %}text-green{% else %}text-red{% endif %}" style="font-family: 'Courier New', monospace; margin-left: 5px;">
                        {{ "{:+,.2f}".format(index_quote.change) }} ({{ "{:+.2f}%".format(index_quote.pct_change) }})
                    </span>
                </span>
                {% endif %}
            </div>"""

html_content = html_content.replace(old_html, new_html)

with open('templates/constituents.html', 'w') as f:
    f.write(html_content)

print('Patched app.py and constituents.html!')
