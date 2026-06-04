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

    function printTerminal(text, type = 'normal') {
        const div = document.createElement('div');
        if (type === 'error') div.className = 'terminal-error';
        else if (type === 'success') div.className = 'terminal-success';
        
        // Ensure newlines render properly
        div.innerHTML = text.replace(/\n/g, '<br>').replace(/ /g, '&nbsp;');
        output.appendChild(div);
        output.scrollTop = output.scrollHeight;
    }

    input.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            const cmd = input.value.trim();
            if (!cmd) return;

            // Add to history
            history.push(cmd);
            historyIdx = history.length;

            // Print prompt
            printTerminal(`> ${cmd}`);
            input.value = '';

            // Handle client-side commands
            if (cmd.toLowerCase() === 'clear') {
                output.innerHTML = '';
                return;
            }

            // Send to backend
            try {
                const response = await fetch('/api/terminal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cmd })
                });

                const data = await response.json();

                if (data.action === 'redirect') {
                    printTerminal(`Redirecting to ${data.url}...`, 'success');
                    window.location.href = data.url;
                } else if (data.action === 'chart') {
                    printTerminal(`Rendering chart for ${data.symbol}...`, 'success');
                    openChartModal(data.symbol, data.data);
                } else if (data.action === 'print') {
                    printTerminal(data.text, data.type || 'normal');
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
