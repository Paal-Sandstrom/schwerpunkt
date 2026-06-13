with open('templates/stock_search.html', 'r') as f:
    content = f.read()

old_script = '''                            div.onmouseover = function() { this.style.backgroundColor = '#eaf2ea'; };
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

new_script = '''                            div.onmouseover = function() { 
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
                });
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
</script>'''

content = content.replace(old_script, new_script)

with open('templates/stock_search.html', 'w') as f:
    f.write(content)
print('stock_search.html patched for keyboard nav!')
