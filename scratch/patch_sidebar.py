with open('templates/constituents.html', 'r') as f:
    content = f.read()

# 1. Remove it from the main header
old_main_header = """            <div class="box-header">
                INDEX {{ index_name|upper }} CONSTITUENTS
                {% if index_quote %}
                <span style="float: right; font-weight: normal; font-size: 11px;">
                    Daily Performance: 
                    <span class="text-bold" style="font-family: 'Courier New', monospace;">{{ "{:,.2f}".format(index_quote.price) }}</span>
                    <span class="{% if index_quote.change >= 0 %}text-green{% else %}text-red{% endif %}" style="font-family: 'Courier New', monospace; margin-left: 5px;">
                        {{ "{:+,.2f}".format(index_quote.change) }} ({{ "{:+.2f}%".format(index_quote.pct_change) }})
                    </span>
                </span>
                {% endif %}
            </div>"""

new_main_header = """            <div class="box-header">INDEX {{ index_name|upper }} CONSTITUENTS</div>"""

content = content.replace(old_main_header, new_main_header)


# 2. Add it above the Sector Concentration Box
old_sidebar = """    <!-- Sidebar Column: Sector Concentration & Top Holdings Charts -->
    <div class="layout-col-side" style="flex: 1; max-width: 320px; min-width: 300px; display: flex; flex-direction: column; gap: 15px;">
        
        <!-- Sector Concentration Box -->
        <div class="box" style="margin-bottom: 0;">
            <div class="box-header">SECTOR WEIGHT (MARKET CAP)</div>"""

new_sidebar = """    <!-- Sidebar Column: Sector Concentration & Top Holdings Charts -->
    <div class="layout-col-side" style="flex: 1; max-width: 320px; min-width: 300px; display: flex; flex-direction: column; gap: 15px;">
        
        {% if index_quote %}
        <!-- Daily Performance Box -->
        <div class="box" style="margin-bottom: 0;">
            <div class="box-header">INDEX PERFORMANCE</div>
            <div class="box-body" style="padding: 20px 10px; text-align: center; background-color: #fcfcfc;">
                <div style="font-size: 26px; font-weight: bold; font-family: 'Courier New', monospace; color: #1f4d1f; letter-spacing: -0.5px;">
                    {{ "{:,.2f}".format(index_quote.price) }}
                </div>
                <div class="{% if index_quote.change >= 0 %}text-green{% else %}text-red{% endif %}" style="margin-top: 5px; font-size: 15px; font-weight: bold; font-family: 'Courier New', monospace;">
                    {{ "{:+,.2f}".format(index_quote.change) }} ({{ "{:+.2f}%".format(index_quote.pct_change) }})
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Sector Concentration Box -->
        <div class="box" style="margin-bottom: 0;">
            <div class="box-header">SECTOR WEIGHT (MARKET CAP)</div>"""

content = content.replace(old_sidebar, new_sidebar)

with open('templates/constituents.html', 'w') as f:
    f.write(content)

print('Moved daily performance to its own box in the sidebar!')
