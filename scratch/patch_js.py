with open('templates/base.html', 'r') as f:
    content = f.read()

old_script = '''                                                div.onmouseover = function() { this.style.backgroundColor = '#eaf2ea'; };
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

new_script = '''                                                div.onmouseover = function() { 
                                                    Array.from(gSearchDropdown.children).forEach(c => c.style.backgroundColor = 'transparent');
                                                    this.style.backgroundColor = '#eaf2ea'; 
                                                };
                                                div.onmouseout = function() { this.style.backgroundColor = 'transparent'; };
                                                
                                                div.onclick = function() {
                                                    gSearchInput.value = item.symbol;
                                                    gSearchDropdown.style.display = 'none';
                                                    gSearchInput.closest('form').submit();
                                                };
                                                gSearchDropdown.appendChild(div);
                                            });
                                            gSearchDropdown.style.display = 'block';
                                            gSearchInput.dataset.activeIndex = -1;
                                        } else {
                                            gSearchDropdown.style.display = 'none';
                                        }
                                    }).catch(e => console.error(e));
                            }, 200);
                        });

                        gSearchInput.addEventListener('keydown', function(e) {
                            if (gSearchDropdown.style.display === 'none') return;
                            
                            const items = Array.from(gSearchDropdown.children);
                            let activeIndex = parseInt(gSearchInput.dataset.activeIndex || -1);

                            if (e.key === 'ArrowDown') {
                                e.preventDefault();
                                activeIndex = (activeIndex + 1) % items.length;
                                updateActiveItem(items, activeIndex);
                            } else if (e.key === 'ArrowUp') {
                                e.preventDefault();
                                activeIndex = (activeIndex - 1 + items.length) % items.length;
                                updateActiveItem(items, activeIndex);
                            } else if (e.key === 'Enter' && activeIndex > -1) {
                                e.preventDefault();
                                items[activeIndex].click();
                            }
                        });

                        function updateActiveItem(items, index) {
                            items.forEach((item, i) => {
                                item.style.backgroundColor = (i === index) ? '#eaf2ea' : 'transparent';
                            });
                            gSearchInput.dataset.activeIndex = index;
                            if (index > -1) {
                                items[index].scrollIntoView({ block: 'nearest' });
                            }
                        }

                        document.addEventListener('click', function(e) {
                            if (!gSearchInput.contains(e.target) && !gSearchDropdown.contains(e.target)) {
                                gSearchDropdown.style.display = 'none';
                            }
                        });
                    }
                });
            </script>'''

content = content.replace(old_script, new_script)

with open('templates/base.html', 'w') as f:
    f.write(content)
print('Base.html patched for keyboard nav!')
