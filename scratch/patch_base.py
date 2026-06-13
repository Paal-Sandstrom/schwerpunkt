with open('templates/base.html', 'r') as f:
    content = f.read()

old_form = '''            <div class="web-search-box">
                <form action="{{ url_for('query_ticker') }}" method="POST" style="display: flex; align-items: center;" id="search-form">
                    <input type="text" id="ticker-input" name="symbol" placeholder="Search Ticker (e.g., AAPL, MSFT, NVDA)..." class="web-search-input" required autocomplete="off">
                    <button type="submit" class="web-search-btn">Query</button>
                </form>
            </div>'''

new_form = '''            <div class="web-search-box">
                <form action="{{ url_for('query_ticker') }}" method="POST" style="display: flex; align-items: center; position: relative;" id="search-form">
                    <input type="text" id="ticker-input" name="symbol" placeholder="Search Ticker or Name..." class="web-search-input" required autocomplete="off">
                    <button type="submit" class="web-search-btn">Query</button>
                    
                    <div id="global-search-dropdown" style="display: none; position: absolute; top: 100%; left: 0; width: 100%; background: white; border: 1px solid #1f4d1f; box-shadow: 0 4px 8px rgba(0,0,0,0.1); z-index: 2000; text-align: left; max-height: 300px; overflow-y: auto;">
                    </div>
                </form>
            </div>
            
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const gSearchInput = document.getElementById('ticker-input');
                    const gSearchDropdown = document.getElementById('global-search-dropdown');
                    let gDebounceTimer;

                    if (gSearchInput && gSearchDropdown) {
                        gSearchInput.addEventListener('input', function() {
                            clearTimeout(gDebounceTimer);
                            const query = this.value.trim();
                            
                            if (query.length < 1) {
                                gSearchDropdown.style.display = 'none';
                                return;
                            }

                            gDebounceTimer = setTimeout(() => {
                                fetch('/api/search?q=' + encodeURIComponent(query))
                                    .then(response => response.json())
                                    .then(data => {
                                        if (data.length > 0) {
                                            gSearchDropdown.innerHTML = '';
                                            data.forEach(item => {
                                                const div = document.createElement('div');
                                                div.style.padding = '8px 10px';
                                                div.style.cursor = 'pointer';
                                                div.style.borderBottom = '1px solid #eee';
                                                div.style.fontFamily = 'Courier New, monospace';
                                                div.style.fontSize = '12px';
                                                div.innerHTML = '<span style="font-weight: bold; color: #1f4d1f;">' + item.symbol + '</span> <span style="color: #666;">- ' + item.name + '</span>';
                                                
                                                div.onmouseover = function() { this.style.backgroundColor = '#eaf2ea'; };
                                                div.onmouseout = function() { this.style.backgroundColor = 'transparent'; };
                                                
                                                div.onclick = function() {
                                                    gSearchInput.value = item.symbol;
                                                    gSearchDropdown.style.display = 'none';
                                                    gSearchInput.closest('form').submit();
                                                };
                                                gSearchDropdown.appendChild(div);
                                            });
                                            gSearchDropdown.style.display = 'block';
                                        } else {
                                            gSearchDropdown.style.display = 'none';
                                        }
                                    }).catch(e => console.error(e));
                            }, 200);
                        });

                        document.addEventListener('click', function(e) {
                            if (!gSearchInput.contains(e.target) && !gSearchDropdown.contains(e.target)) {
                                gSearchDropdown.style.display = 'none';
                            }
                        });
                    }
                });
            </script>'''

content = content.replace(old_form, new_form)

with open('templates/base.html', 'w') as f:
    f.write(content)
print('Base.html patched!')
