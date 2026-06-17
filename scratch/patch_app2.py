with open('app.py', 'r') as f:
    app_code = f.read()

route_code = '''
@app.route('/screener')
def screener():
    return render_template('screener.html')
'''

if '/screener' not in app_code:
    app_code = app_code.replace("def guide():", route_code + "\n@app.route('/guide')\ndef guide():")

with open('app.py', 'w') as f:
    f.write(app_code)

with open('templates/base.html', 'r') as f:
    base_code = f.read()

screener_link = '<a href="{{ url_for(\'screener\') }}" class="web-nav-item">Screener</a>'

if 'Screener</a>' not in base_code:
    base_code = base_code.replace('<a href="{{ url_for(\'guide\') }}"', screener_link + '\n                    <a href="{{ url_for(\'guide\') }}"')

with open('templates/base.html', 'w') as f:
    f.write(base_code)

print('Patched app.py and base.html with screener route.')
