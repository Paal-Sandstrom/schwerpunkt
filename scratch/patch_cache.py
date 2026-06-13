with open('templates/base.html', 'r') as f:
    content = f.read()

content = content.replace("fetch('/api/search?q=' + encodeURIComponent(query))", "fetch('/api/search?q=' + encodeURIComponent(query) + '&_t=' + new Date().getTime())")

with open('templates/base.html', 'w') as f:
    f.write(content)

with open('templates/stock_search.html', 'r') as f:
    content2 = f.read()

content2 = content2.replace("fetch('/api/search?q=' + encodeURIComponent(query))", "fetch('/api/search?q=' + encodeURIComponent(query) + '&_t=' + new Date().getTime())")

with open('templates/stock_search.html', 'w') as f:
    f.write(content2)

print('Added cache buster to fetch requests')
