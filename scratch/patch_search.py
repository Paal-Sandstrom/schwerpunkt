with open('templates/stock_search.html', 'r') as f:
    content = f.read()

old_form = '''        <form action="{{ url_for('query_ticker') }}" method="POST" style="display: flex; justify-content: center; margin-bottom: 40px;">
            <input type="text" name="symbol" placeholder="e.g. AAPL, MSFT, TSLA..." 
                   style="width: 50%; padding: 10px; font-size: 16px; font-family: Courier New, Courier, monospace; 
                          border: 2px solid #1f4d1f; border-radius: 0px; outline: none; box-shadow: inset 2px 2px 5px rgba(0,0,0,0.1);" 
                   required autocomplete="off" autofocus>
            <button type="submit" class="btn-primary" style="margin-left: 10px; padding: 0 20px; font-size: 14px; border-radius: 0px;">Search</button>
        </form>'''

new_form = '''        <form action="{{ url_for('query_ticker') }}" method="POST" style="display: flex; justify-content: center; margin-bottom: 40px; align-items: flex-start;">
            <div style="position: relative; width: 50%;">
                <input type="text" name="symbol" id="search-input" placeholder="e.g. AAPL, Toyota, Sony..." 
                       style="width: 100%; box-sizing: border-box; padding: 10px; font-size: 16px; font-family: Courier New, Courier, monospace; 
                              border: 2px solid #1f4d1f; border-radius: 0px; outline: none; box-shadow: inset 2px 2px 5px rgba(0,0,0,0.1);" 
                       required autocomplete="off" autofocus>
                
                <div id="search-dropdown" style="display: none; position: absolute; top: 100%; left: 0; width: 100%; background: white; border: 1px solid #1f4d1f; box-shadow: 0 4px 8px rgba(0,0,0,0.1); z-index: 1000; text-align: left; max-height: 250px; overflow-y: auto;">
                </div>
            </div>
            <button type="submit" class="btn-primary" style="margin-left: 10px; padding: 10px 20px; font-size: 14px; border-radius: 0px; height: 43px;">Search</button>
        </form>

<script>
    const searchInput = document.getElementById('search-input');
    const searchDropdown = document.getElementById('search-dropdown');
    let debounceTimer;

    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const query = this.value.trim();
        
        if (query.length < 1) {
            searchDropdown.style.display = 'none';
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch('/api/search?q=' + encodeURIComponent(query))
                .then(response => response.json())
                .then(data => {
                    if (data.length > 0) {
                        searchDropdown.innerHTML = '';
                        data.forEach(item => {
                            const div = document.createElement('div');
                            div.style.padding = '8px 10px';
                            div.style.cursor = 'pointer';
                            div.style.borderBottom = '1px solid #eee';
                            div.style.fontFamily = 'Courier New, monospace';
                            div.innerHTML = '<span style="font-weight: bold; color: #1f4d1f;">' + item.symbol + '</span> <span style="color: #666; font-size: 12px;">- ' + item.name + '</span>';
                            
                            div.onmouseover = function() { this.style.backgroundColor = '#eaf2ea'; };
                            div.onmouseout = function() { this.style.backgroundColor = 'transparent'; };
                            
                            div.onclick = function() {
                                searchInput.value = item.symbol;
                                searchDropdown.style.display = 'none';
                                searchInput.closest('form').submit();
                            };
                            searchDropdown.appendChild(div);
                        });
                        searchDropdown.style.display = 'block';
                    } else {
                        searchDropdown.style.display = 'none';
                    }
                });
        }, 200);
    });

    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
            searchDropdown.style.display = 'none';
        }
    });
</script>'''

content = content.replace(old_form, new_form)

with open('templates/stock_search.html', 'w') as f:
    f.write(content)
print('Search html updated')
