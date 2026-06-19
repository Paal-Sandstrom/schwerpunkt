import json
import time
import concurrent.futures
import yfinance as yf

keys_to_add = ['industry', 'country', 'exchange', 'forwardPE', 'priceToBook', 'priceToSalesTrailing12Months', 'enterpriseToEbitda', 'profitMargins', 'operatingMargins', 'returnOnEquity', 'returnOnAssets', 'debtToEquity', 'currentRatio', 'revenueGrowth', 'earningsGrowth', 'dividendYield', 'dividendRate', 'payoutRatio']

with open('static/index_data.json', 'r') as f:
    data = json.load(f)

# Extract symbols that are missing the 'country' field
missing_symbols = set()
for idx_key in data:
    for item in data[idx_key]['constituents']:
        if not item.get('country'):
            missing_symbols.add(item['symbol'])

print(f"Fetching extra info for {len(missing_symbols)} missing symbols...")

def fetch_info(sym):
    try:
        time.sleep(0.1) # Small delay to avoid burst rate limit
        info = yf.Ticker(sym).info
        if not info or 'country' not in info:
            return None
            
        res = {'symbol': sym}
        for k in keys_to_add:
            res[k] = info.get(k)
        return res
    except Exception as e:
        return None

results = {}
count = 0
# Use a low number of workers to avoid 401 Unauthorized IP ban
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(fetch_info, sym): sym for sym in missing_symbols}
    for fut in concurrent.futures.as_completed(futures):
        res = fut.result()
        if res:
            results[res['symbol']] = res
        count += 1
        if count % 100 == 0:
            print(f"Processed {count}/{len(missing_symbols)}")

for idx_key in data:
    for item in data[idx_key]['constituents']:
        sym = item['symbol']
        if sym in results:
            for k in keys_to_add:
                item[k] = results[sym].get(k)

with open('static/index_data.json', 'w') as f:
    json.dump(data, f)
print("Updated index_data.json successfully with missing data.")
