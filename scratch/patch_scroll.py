with open('templates/ticker.html', 'r') as f:
    content = f.read()

old_script = '''<script>
    document.addEventListener('DOMContentLoaded', () => {
        // Safe check for chart_data (defined only in overview subview, empty otherwise)
        const chartData = {{ (chart_data or []) | tojson | safe }};
        const canvas = document.getElementById('ticker-chart');
        if (canvas && chartData && chartData.length) {
            new StockChart(canvas, chartData);
        }
    });
</script>'''

new_script = '''<script>
    document.addEventListener('DOMContentLoaded', () => {
        // Safe check for chart_data (defined only in overview subview, empty otherwise)
        const chartData = {{ (chart_data or []) | tojson | safe }};
        const canvas = document.getElementById('ticker-chart');
        if (canvas && chartData && chartData.length) {
            new StockChart(canvas, chartData);
        }
        
        // Scroll restoration logic to prevent page jumping on tab or period changes
        const scrollKey = 'scrollPos_' + window.location.pathname;
        const savedScroll = sessionStorage.getItem(scrollKey);
        if (savedScroll) {
            // Slight delay ensures the DOM layout is fully calculated before jumping
            setTimeout(() => window.scrollTo(0, parseInt(savedScroll, 10)), 10);
            sessionStorage.removeItem(scrollKey);
        }

        window.addEventListener("beforeunload", function() {
            sessionStorage.setItem(scrollKey, window.scrollY);
        });
    });
</script>'''

content = content.replace(old_script, new_script)

with open('templates/ticker.html', 'w') as f:
    f.write(content)

print('Scroll restoration added to ticker.html!')
