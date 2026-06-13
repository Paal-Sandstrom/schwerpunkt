with open('app.py', 'r') as f:
    content = f.read()

old_mock = '''def get_economic_calendar_mock():
    """Returns a realistic mock economic calendar for the retro UI."""
    return [
        {"date": "Mon 08:30 AM", "event": "Core CPI (MoM)", "impact": "High", "actual": "0.3%", "forecast": "0.3%"},
        {"date": "Mon 08:30 AM", "event": "CPI (YoY)", "impact": "High", "actual": "3.1%", "forecast": "3.1%"},
        {"date": "Tue 10:00 AM", "event": "CB Consumer Confidence", "impact": "Med", "actual": "104.2", "forecast": "101.5"},
        {"date": "Wed 02:00 PM", "event": "FOMC Economic Projections", "impact": "High", "actual": "-", "forecast": "-"},
        {"date": "Wed 02:00 PM", "event": "Fed Interest Rate Decision", "impact": "High", "actual": "-", "forecast": "5.50%"},
        {"date": "Wed 02:30 PM", "event": "FOMC Press Conference", "impact": "High", "actual": "-", "forecast": "-"},
        {"date": "Thu 08:30 AM", "event": "Initial Jobless Claims", "impact": "Med", "actual": "-", "forecast": "215K"},
        {"date": "Thu 08:30 AM", "event": "Retail Sales (MoM)", "impact": "High", "actual": "-", "forecast": "0.4%"},
        {"date": "Fri 09:45 AM", "event": "S&P Global Manufacturing PMI", "impact": "Med", "actual": "-", "forecast": "50.2"}
    ]'''

new_live = '''def get_economic_calendar_mock():
    """Returns a realistic mock economic calendar for the retro UI."""
    return [
        {"date": "Mon 08:30 AM", "event": "Core CPI (MoM)", "impact": "High", "actual": "0.3%", "forecast": "0.3%"},
        {"date": "Mon 08:30 AM", "event": "CPI (YoY)", "impact": "High", "actual": "3.1%", "forecast": "3.1%"},
        {"date": "Tue 10:00 AM", "event": "CB Consumer Confidence", "impact": "Med", "actual": "104.2", "forecast": "101.5"},
        {"date": "Wed 02:00 PM", "event": "FOMC Economic Projections", "impact": "High", "actual": "-", "forecast": "-"},
        {"date": "Wed 02:00 PM", "event": "Fed Interest Rate Decision", "impact": "High", "actual": "-", "forecast": "5.50%"},
        {"date": "Wed 02:30 PM", "event": "FOMC Press Conference", "impact": "High", "actual": "-", "forecast": "-"},
        {"date": "Thu 08:30 AM", "event": "Initial Jobless Claims", "impact": "Med", "actual": "-", "forecast": "215K"},
        {"date": "Thu 08:30 AM", "event": "Retail Sales (MoM)", "impact": "High", "actual": "-", "forecast": "0.4%"},
        {"date": "Fri 09:45 AM", "event": "S&P Global Manufacturing PMI", "impact": "Med", "actual": "-", "forecast": "50.2"}
    ]

def get_economic_calendar_live():
    """Fetch live economic calendar from Yahoo Finance."""
    cache_key = "economic_calendar_live"
    cached = app_cache.get(cache_key)
    if cached:
        return cached

    import requests
    from bs4 import BeautifulSoup
    import datetime
    
    events = []
    base_date = datetime.date.today()
    
    try:
        for i in range(7):
            d = base_date + datetime.timedelta(days=i)
            if d.weekday() >= 5: continue # Skip weekends
            
            url = f"https://finance.yahoo.com/calendar/economic?day={d.strftime('%Y-%m-%d')}"
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table')
            
            if table:
                for r in table.find_all('tr')[1:]:
                    cols = r.find_all('td')
                    if len(cols) >= 7:
                        event = cols[0].text.strip()
                        country = cols[1].text.strip()
                        time_val = cols[2].text.strip()
                        actual = cols[4].text.strip()
                        forecast = cols[5].text.strip()
                        
                        if country in ['US', 'EU', 'GB', 'JP', 'DE']:
                            impact = 'High' if any(x in event for x in ['GDP', 'CPI', 'Fed', 'Interest', 'Employment', 'Payroll', 'Jobless']) else 'Med'
                            events.append({
                                'date': f"{d.strftime('%a')} {time_val.replace('UTC', '').strip()}",
                                'event': f"[{country}] {event[:35]}",
                                'impact': impact,
                                'actual': actual,
                                'forecast': forecast
                            })
                            
                            if len(events) >= 8: break
            if len(events) >= 8: break
    except Exception as e:
        print(f"Calendar fetch error: {e}")
        
    if not events:
        events = get_economic_calendar_mock()
        
    app_cache.set(cache_key, events, ttl=3600) # 1 hour cache
    return events'''

content = content.replace(old_mock, new_live)
content = content.replace('economic_calendar = get_economic_calendar_mock()', 'economic_calendar = get_economic_calendar_live()')

with open('app.py', 'w') as f:
    f.write(content)

print('Patched app.py with live economic calendar!')
