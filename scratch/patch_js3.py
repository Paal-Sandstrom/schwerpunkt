with open('templates/stock_search.html', 'r') as f:
    content = f.read()

import re
old_script_block = re.search(r'<script>.*?</script>', content, flags=re.DOTALL).group(0)

new_script_block = '''<script>
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchDropdown = document.getElementById('search-dropdown');
    let debounceTimer;

    if (!searchInput || !searchDropdown) return;

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
                            
                            div.onmouseover = function() { 
                                Array.from(searchDropdown.children).forEach(c => c.style.backgroundColor = 'transparent');
                                this.style.backgroundColor = '#eaf2ea'; 
                            };
                            div.onmouseout = function() { this.style.backgroundColor = 'transparent'; };
                            
                            div.onclick = function() {
                                searchInput.value = item.symbol;
                                searchDropdown.style.display = 'none';
                                searchInput.closest('form').submit();
                            };
                            searchDropdown.appendChild(div);
                        });
                        searchDropdown.style.display = 'block';
                        searchInput.dataset.activeIndex = -1;
                    } else {
                        searchDropdown.style.display = 'none';
                    }
                }).catch(e => console.error(e));
        }, 200);
    });

    searchInput.addEventListener('keydown', function(e) {
        if (searchDropdown.style.display === 'none') return;
        
        const items = Array.from(searchDropdown.children);
        let activeIndex = parseInt(searchInput.dataset.activeIndex || -1);

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = (activeIndex + 1) % items.length;
            updateActiveItemSearch(items, activeIndex);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = (activeIndex - 1 + items.length) % items.length;
            updateActiveItemSearch(items, activeIndex);
        } else if (e.key === 'Enter' && activeIndex > -1) {
            e.preventDefault();
            items[activeIndex].click();
        }
    });

    function updateActiveItemSearch(items, index) {
        items.forEach((item, i) => {
            item.style.backgroundColor = (i === index) ? '#eaf2ea' : 'transparent';
        });
        searchInput.dataset.activeIndex = index;
        if (index > -1) {
            items[index].scrollIntoView({ block: 'nearest' });
        }
    }

    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
            searchDropdown.style.display = 'none';
        }
    });
});
</script>'''

content = content.replace(old_script_block, new_script_block)

with open('templates/stock_search.html', 'w') as f:
    f.write(content)
print('stock_search.html fully wrapped in DOMContentLoaded')
