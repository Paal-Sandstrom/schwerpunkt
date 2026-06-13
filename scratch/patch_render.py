with open('app.py', 'r') as f:
    content = f.read()

old_str = """    return render_template(
        'constituents.html',
        index_id=index_id,
        index_name=index_name,
        constituents=formatted_constituents,"""

new_str = """    return render_template(
        'constituents.html',
        index_id=index_id,
        index_name=index_name,
        index_quote=index_quote,
        constituents=formatted_constituents,"""

content = content.replace(old_str, new_str)

with open('app.py', 'w') as f:
    f.write(content)

print('Patched app.py render payload!')
