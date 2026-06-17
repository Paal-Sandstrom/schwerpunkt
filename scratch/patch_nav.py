with open('templates/base.html', 'r') as f:
    base_code = f.read()

screener_link = '<a href="{{ url_for(\'screener\') }}" class="web-nav-link {% if request.path == \'/screener\' %}active{% endif %}">Screener</a>'
guide_link = '<a href="{{ url_for(\'guide_view\') }}"'

if 'Screener</a>' not in base_code:
    base_code = base_code.replace(guide_link, screener_link + '\n                ' + guide_link)
    with open('templates/base.html', 'w') as f:
        f.write(base_code)
    print('Patched base.html')

with open('app.py', 'r') as f:
    app_code = f.read()

help_old = "- nav [ticker] : Navigate main window to ticker page"
help_new = "- nav [ticker|screener|home] : Navigate main window\n                - screener : Open stock screener"
if help_new not in app_code:
    app_code = app_code.replace(help_old, help_new)

nav_old = "elif target == 'guide':"
nav_new = "elif target == 'screener':\n                return jsonify({'action': 'redirect', 'url': url_for('screener')})\n            elif target == 'guide':"
if "target == 'screener':" not in app_code:
    app_code = app_code.replace(nav_old, nav_new)
    
# also add `screener` command natively
cmd_old = "elif action == 'nav' and len(parts) > 1:"
cmd_new = "elif action == 'screener':\n            return jsonify({'action': 'redirect', 'url': url_for('screener')})\n        elif action == 'nav' and len(parts) > 1:"
if "elif action == 'screener':" not in app_code:
    app_code = app_code.replace(cmd_old, cmd_new)

with open('app.py', 'w') as f:
    f.write(app_code)
print('Patched app.py')
