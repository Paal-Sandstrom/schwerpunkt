with open('templates/base.html', 'r') as f:
    content = f.read()

old_base_script = """        // Immediately apply saved terminal position before body renders to avoid flickering
        const savedX = localStorage.getItem('terminal_x');
        const savedY = localStorage.getItem('terminal_y');
        if (savedX !== null && savedY !== null) {
            const style = document.createElement('style');
            style.innerHTML = `#floating-terminal { left: ${savedX}px; top: ${savedY}px; margin: 0; right: auto; bottom: auto; }`;
            document.head.appendChild(style);
        }"""

new_base_script = """        // Immediately apply saved terminal position before body renders to avoid flickering
        let savedX = parseInt(localStorage.getItem('terminal_x'));
        let savedY = parseInt(localStorage.getItem('terminal_y'));
        if (!isNaN(savedX) && !isNaN(savedY)) {
            const maxX = window.innerWidth - 320;
            const maxY = window.innerHeight - 50;
            if (savedX > maxX) savedX = Math.max(0, maxX);
            if (savedY > maxY) savedY = Math.max(0, maxY);
            if (savedX < 0) savedX = 0;
            if (savedY < 0) savedY = 0;
            
            const style = document.createElement('style');
            style.innerHTML = `#floating-terminal { left: ${savedX}px; top: ${savedY}px; margin: 0; right: auto; bottom: auto; }`;
            document.head.appendChild(style);
        }"""

content = content.replace(old_base_script, new_base_script)

with open('templates/base.html', 'w') as f:
    f.write(content)

with open('static/terminal.js', 'r') as f:
    term_content = f.read()

old_term_script = """        // Fallback positioning if no localStorage exists
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
        }"""

new_term_script = """        // Fallback positioning if no localStorage exists
        let savedX = parseInt(localStorage.getItem('terminal_x'));
        let savedY = parseInt(localStorage.getItem('terminal_y'));
        
        if (isNaN(savedX) || isNaN(savedY)) {
            terminalNode.style.right = '20px';
            terminalNode.style.top = '80px';
            terminalNode.style.margin = '0';
        } else {
            const maxX = window.innerWidth - 320;
            const maxY = window.innerHeight - 50;
            if (savedX > maxX) savedX = Math.max(0, maxX);
            if (savedY > maxY) savedY = Math.max(0, maxY);
            if (savedX < 0) savedX = 0;
            if (savedY < 0) savedY = 0;
            
            terminalNode.style.left = savedX + 'px';
            terminalNode.style.top = savedY + 'px';
            terminalNode.style.margin = '0';
            terminalNode.style.right = 'auto';
            terminalNode.style.bottom = 'auto';
        }"""

term_content = term_content.replace(old_term_script, new_term_script)

with open('static/terminal.js', 'w') as f:
    f.write(term_content)

print('Patched base.html and terminal.js!')
