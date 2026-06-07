// Schwerpunkt Interactive Terminal Controller

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('terminal-input');
    const output = document.getElementById('terminal-output');
    
    if (!input || !output) return;

    const history = [];
    let historyIdx = -1;

    // Focus input when clicking anywhere in terminal
    document.querySelector('.app-terminal').addEventListener('click', () => {
        input.focus();
    });

    // Auto-focus if we just navigated here via a terminal command
    if (sessionStorage.getItem('focus_terminal_on_load') === 'true') {
        input.focus();
        sessionStorage.removeItem('focus_terminal_on_load');
    }

    // ----------------------------------------------------
    // Floating Terminal Drag & Drop Logic
    // ----------------------------------------------------
    const terminalNode = document.getElementById('floating-terminal');
    const dragHandle = document.getElementById('terminal-drag-handle');
    
    if (terminalNode && dragHandle) {
        // Fallback positioning if no localStorage exists
        const savedX = localStorage.getItem('terminal_x');
        const savedY = localStorage.getItem('terminal_y');
        
        if (!savedX || !savedY) {
            terminalNode.style.right = '20px';
            terminalNode.style.top = '80px';
            terminalNode.style.margin = '0';
        } else {
            terminalNode.style.left = savedX + 'px';
            terminalNode.style.top = savedY + 'px';
            terminalNode.style.margin = '0';
            terminalNode.style.right = 'auto';
            terminalNode.style.bottom = 'auto';
        }

        let isDragging = false;
        let startX, startY, initialLeft, initialTop;

        dragHandle.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            
            const rect = terminalNode.getBoundingClientRect();
            initialLeft = rect.left;
            initialTop = rect.top;
            
            // Clear right/bottom so left/top changes actually apply
            terminalNode.style.right = 'auto';
            terminalNode.style.bottom = 'auto';
            terminalNode.style.left = initialLeft + 'px';
            terminalNode.style.top = initialTop + 'px';
            
            // Prevent text selection while dragging
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            
            terminalNode.style.left = (initialLeft + dx) + 'px';
            terminalNode.style.top = (initialTop + dy) + 'px';
        });

        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                document.body.style.userSelect = '';
                
                const rect = terminalNode.getBoundingClientRect();
                localStorage.setItem('terminal_x', rect.left);
                localStorage.setItem('terminal_y', rect.top);
            }
        });
    }

    function printTerminal(text, type = 'normal') {
        const div = document.createElement('div');
        if (type === 'error') div.className = 'terminal-error';
        else if (type === 'success') div.className = 'terminal-success';
        
        // Ensure newlines render properly
        div.innerHTML = text.replace(/\n/g, '<br>').replace(/ /g, '&nbsp;');
        output.appendChild(div);
        output.scrollTop = output.scrollHeight;
    }

    let currentPrompt = '>';

    input.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            const cmd = input.value.trim();
            if (!cmd) return;

            // Add to history
            history.push(cmd);
            historyIdx = history.length;

            // Print prompt
            printTerminal(`${currentPrompt} ${cmd}`);
            input.value = '';

            // Handle client-side commands
            if (cmd.toLowerCase() === 'clear') {
                output.innerHTML = '';
                return;
            } else if (cmd.toLowerCase() === 'panic' || cmd.toLowerCase() === '/panic') {
                input.disabled = true;
                const origBg = document.body.style.backgroundColor;
                document.body.style.backgroundColor = '#5c0000';
                
                let chaoticText = setInterval(() => {
                    printTerminal(Math.random().toString(36).substring(2, 15).toUpperCase() + ' ALARM TRIGGERED', 'error');
                }, 100);

                setTimeout(() => {
                    clearInterval(chaoticText);
                    document.body.style.backgroundColor = origBg;
                    input.disabled = false;
                    input.focus();
                    printTerminal('System restored. Liquidated all assets successfully.', 'success');
                }, 3000);
                return;
            }

            // LocalStorage Implementation for Research Projects
            const parts = cmd.split(' ');
            const action = parts[0].toLowerCase();
            
            let folders = JSON.parse(localStorage.getItem('schwerpunkt_folders') || '[]');
            let activeFolderId = sessionStorage.getItem('active_folder_id');

            if (['mkdir', 'cd', 'ls', 'note', 'rm', 'cat'].includes(action)) {
                if (action === 'mkdir') {
                    if (parts.length < 2) {
                        printTerminal('Usage: mkdir <foldername>', 'error');
                        return;
                    }
                    const name = parts[1];
                    if (folders.find(f => f.name === name)) {
                        printTerminal(`Folder ${name} already exists.`, 'error');
                        return;
                    }
                    folders.push({ id: Date.now(), name: name, created_at: new Date().toISOString() });
                    localStorage.setItem('schwerpunkt_folders', JSON.stringify(folders));
                    printTerminal(`Created folder ${name}.`, 'success');
                    if(window.refreshFolderList) window.refreshFolderList();
                    return;
                } else if (action === 'cd') {
                    if (parts.length < 2 || parts[1] === '..') {
                        sessionStorage.removeItem('active_folder_id');
                        currentPrompt = '>';
                        printTerminal('Reset to root directory.', 'success');
                        return;
                    }
                    const name = parts[1];
                    const folder = folders.find(f => f.name === name);
                    if (folder) {
                        sessionStorage.setItem('active_folder_id', folder.id);
                        currentPrompt = `${folder.name} >`;
                        printTerminal(`Entered folder ${folder.name}`, 'success');
                    } else {
                        printTerminal(`Folder ${name} not found.`, 'error');
                    }
                    return;
                } else if (action === 'ls') {
                    if (!activeFolderId) {
                        if (folders.length === 0) {
                            printTerminal('No folders found. Use mkdir <foldername> to create one.');
                        } else {
                            printTerminal("Folders:\n  " + folders.map(f => f.name).join("  "));
                        }
                    } else {
                        const folder = folders.find(f => f.id == activeFolderId);
                        if (!folder || !folder.notes || folder.notes.length === 0) {
                            printTerminal('No notes in this folder.');
                        } else {
                            let lines = folder.notes.map(n => {
                                let sentiment = n.sentiment !== 'neutral' ? `[${n.sentiment.toUpperCase()}] ` : '';
                                let priceTag = n.price ? ` (Price @ Creation: $${n.price})` : '';
                                return `Note ${n.id}: ${sentiment}${n.content}${priceTag}`;
                            });
                            printTerminal(lines.join('\n'));
                        }
                    }
                    return;
                } else if (action === 'note') {
                    if (!activeFolderId) {
                        printTerminal('You must be inside a folder to create a note. Use cd <foldername>.', 'error');
                        return;
                    }
                    let sentiment = 'neutral';
                    let args = parts.slice(1);
                    if (args.length > 0 && ['--bullish', '--bearish', '--neutral'].includes(args[0])) {
                        sentiment = args[0].replace('--', '');
                        args = args.slice(1);
                    }
                    let content = args.join(" ");
                    let title = "UNTITLED NOTE";
                    let titleMatch = content.match(/^"([^"]+)"\s*(.*)$/);
                    if (titleMatch) {
                        title = titleMatch[1].toUpperCase();
                        content = titleMatch[2];
                    }
                    if (!content && !titleMatch) {
                        printTerminal('Usage: note [--bullish|--bearish] ["Title"] <content>', 'error');
                        return;
                    }
                    let folderIndex = folders.findIndex(f => f.id == activeFolderId);
                    if (folderIndex !== -1) {
                        if (!folders[folderIndex].notes) folders[folderIndex].notes = [];
                        folders[folderIndex].notes.push({
                            id: Date.now(),
                            title: title,
                            content: content,
                            sentiment: sentiment,
                            price: null, // Cashtag pricing requires backend, disabled for privacy
                            created_at: new Date().toISOString().slice(0,16)
                        });
                        localStorage.setItem('schwerpunkt_folders', JSON.stringify(folders));
                        printTerminal(`Note "${title}" saved successfully.`, 'success');
                        if(window.refreshFolderList) window.refreshFolderList();
                        if(window.currentFolderId == activeFolderId && window.openFolderDossier) window.openFolderDossier(folders[folderIndex].id, folders[folderIndex].name);
                    }
                    return;
                } else if (action === 'rm') {
                    if (parts.length < 2) {
                        printTerminal('Usage: rm <foldername> or rm <note_id>', 'error');
                        return;
                    }
                    const target = parts[1];
                    if (isNaN(target)) { // Delete folder
                        const initialLength = folders.length;
                        folders = folders.filter(f => f.name !== target);
                        if (folders.length < initialLength) {
                            localStorage.setItem('schwerpunkt_folders', JSON.stringify(folders));
                            printTerminal(`Deleted folder ${target} and its notes.`, 'success');
                            if(window.refreshFolderList) window.refreshFolderList();
                        } else {
                            printTerminal(`Folder ${target} not found.`, 'error');
                        }
                    } else { // Delete note
                        if (activeFolderId) {
                            let folder = folders.find(f => f.id == activeFolderId);
                            if (folder && folder.notes) {
                                folder.notes = folder.notes.filter(n => n.id != target);
                                localStorage.setItem('schwerpunkt_folders', JSON.stringify(folders));
                                printTerminal(`Deleted note ${target}.`, 'success');
                                if(window.refreshFolderList) window.refreshFolderList();
                                if(window.currentFolderId == activeFolderId && window.openFolderDossier) window.openFolderDossier(folder.id, folder.name);
                            }
                        } else {
                            printTerminal('Enter a folder first to delete a note.', 'error');
                        }
                    }
                    return;
                } else if (action === 'cat') {
                     if (parts.length < 2) {
                        printTerminal('Usage: cat <note_id>', 'error');
                        return;
                    }
                    const noteId = parts[1];
                    let foundNote = null;
                    folders.forEach(f => { if(f.notes) { let n = f.notes.find(x => x.id == noteId); if(n) foundNote = n; } });
                    if (foundNote) {
                        let sent = foundNote.sentiment !== 'neutral' ? `[${foundNote.sentiment.toUpperCase()}]` : '';
                        let text = `--- Note ${foundNote.id} ---\nCreated: ${foundNote.created_at}\nSentiment: ${sent}\n\n${foundNote.content}\n-------------------`;
                        printTerminal(text);
                    } else {
                        printTerminal(`Note ${noteId} not found.`, 'error');
                    }
                    return;
                }
            }

            // Send financial commands to backend
            try {
                const response = await fetch('/api/terminal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cmd })
                });

                const data = await response.json();

                if (data.action === 'redirect') {
                    printTerminal(`Redirecting to ${data.url}...`, 'success');
                    sessionStorage.setItem('focus_terminal_on_load', 'true');
                    window.location.href = data.url;
                } else if (data.action === 'chart') {
                    printTerminal(`Rendering chart for ${data.symbol}...`, 'success');
                    openChartModal(data.symbol, data.data, data.period);
                } else if (data.action === 'statement') {
                    printTerminal(`Rendering ${data.title}...`, 'success');
                    openStatementModal(data.title, data.headers, data.rows);
                } else if (data.action === 'print') {
                    printTerminal(data.text, data.type || 'normal');
                } else if (data.action === 'cd') {
                    printTerminal(data.text, 'success');
                    if (data.prompt) currentPrompt = data.prompt;
                } else if (data.error) {
                    printTerminal(`Error: ${data.error}`, 'error');
                } else {
                    printTerminal('Unrecognized response from server.', 'error');
                }
            } catch (err) {
                printTerminal('Connection to terminal server lost.', 'error');
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (historyIdx > 0) {
                historyIdx--;
                input.value = history[historyIdx];
            }
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (historyIdx < history.length - 1) {
                historyIdx++;
                input.value = history[historyIdx];
            } else {
                historyIdx = history.length;
                input.value = '';
            }
        }
    });

    // Modal Period Buttons
    document.querySelectorAll('.terminal-chart-period').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!currentChartSymbol) return;
            const period = btn.getAttribute('data-period');
            const cmd = `chart ${currentChartSymbol} ${period}`;
            
            try {
                const response = await fetch('/api/terminal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cmd })
                });

                const data = await response.json();
                if (data.action === 'chart') {
                    openChartModal(data.symbol, data.data, data.period || period);
                } else if (data.error) {
                    printTerminal(`Error: ${data.error}`, 'error');
                }
            } catch (err) {
                printTerminal('Connection to terminal server lost.', 'error');
            }
        });
    });
});

// --- Modal Chart Logic ---
let terminalChartInstance = null;
let currentChartSymbol = '';

window.openChartModal = function(symbol, chartData, period = '1y') {
    currentChartSymbol = symbol;
    
    // Update active period button
    document.querySelectorAll('.terminal-chart-period').forEach(btn => {
        if (btn.getAttribute('data-period') === period) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    const modal = document.getElementById('chart-modal');
    const title = document.getElementById('chart-modal-title');
    const canvas = document.getElementById('terminal-chart-canvas');
    
    title.textContent = `Chart Viewer - ${symbol.toUpperCase()}`;
    modal.style.display = 'flex';
    
    // Slight delay to allow modal display so canvas has dimensions
    setTimeout(() => {
        // Recreate canvas to clear any previous bindings (StockChart overrides scale)
        const parent = canvas.parentNode;
        parent.removeChild(canvas);
        const newCanvas = document.createElement('canvas');
        newCanvas.id = 'terminal-chart-canvas';
        newCanvas.style.width = '100%';
        newCanvas.style.height = '400px';
        newCanvas.style.display = 'block';
        parent.appendChild(newCanvas);
        
        terminalChartInstance = new StockChart(newCanvas, chartData);
    }, 50);
}

window.closeChartModal = function() {
    document.getElementById('chart-modal').style.display = 'none';
}

window.saveChartImage = function() {
    const canvas = document.getElementById('terminal-chart-canvas');
    if (!canvas) return;
    
    const link = document.createElement('a');
    link.download = `chart_${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
}

// --- Modal Statement Logic ---
window.openStatementModal = function(title, headers, rows) {
    const modal = document.getElementById('statement-modal');
    const titleEl = document.getElementById('statement-modal-title');
    const thead = document.getElementById('statement-thead');
    const tbody = document.getElementById('statement-tbody');
    
    titleEl.textContent = title;
    
    // Clear old data
    thead.innerHTML = '';
    tbody.innerHTML = '';
    
    // Build headers
    let headerRow = '<tr><th>Metric</th>';
    for (let h of headers) {
        headerRow += `<th>${h}</th>`;
    }
    headerRow += '</tr>';
    thead.innerHTML = headerRow;
    
    // Build rows
    for (let row of rows) {
        let tr = document.createElement('tr');
        let label = (row[0] || '').toLowerCase();
        let isTotal = label.includes('total') || label.includes('net income') || label.includes('cash and cash equivalents') || label.includes('gross profit');
        
        for (let i = 0; i < row.length; i++) {
            let td = document.createElement('td');
            td.textContent = row[i];
            
            if (i > 0) {
                // Numbers
                td.style.textAlign = 'right';
                td.style.fontFamily = "'Courier New', Courier, monospace";
            } else {
                // Label
                if (isTotal) td.style.fontWeight = 'bold';
            }
            
            if (isTotal && i > 0) {
                td.style.borderTop = '1px solid #000000';
                td.style.borderBottom = '3px double #000000';
                td.style.fontWeight = 'bold';
            }
            tr.appendChild(td);
        }
        tbody.appendChild(tr);
    }
    
    modal.style.display = 'flex';
}

window.closeStatementModal = function() {
    document.getElementById('statement-modal').style.display = 'none';
}
