with open('app.py', 'r') as f:
    content = f.read()

import re

search_code = '''
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
'''

content = content.replace("@app.route('/')", search_code)

with open('app.py', 'w') as f:
    f.write(content)
print('Done!')
