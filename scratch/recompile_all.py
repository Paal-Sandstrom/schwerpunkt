import json
import time
import concurrent.futures
import yfinance as yf

keys_to_add = ['industry', 'country', 'exchange', 'forwardPE', 'priceToBook', 'priceToSalesTrailing12Months', 'enterpriseToEbitda', 'profitMargins', 'operatingMargins', 'returnOnEquity', 'returnOnAssets', 'debtToEquity', 'currentRatio', 'revenueGrowth', 'earningsGrowth', 'dividendYield', 'dividendRate', 'payoutRatio']

with open('static/index_data.json', 'r') as f:
    data = json.load(f)

# Extract unique symbols
symbols = set()
for idx_key in data:
    for item in data[idx_key]['constituents']:
        symbols.add(item['symbol'])

print(f"Fetching extra info for {len(symbols)} symbols...")

def fetch_info(sym):
    try:
        info = yf.Ticker(sym).info
        res = {'symbol': sym}
        for k in keys_to_add:
            res[k] = info.get(k)
        return res
    except:
        return None

results = {}
count = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
    futures = {executor.submit(fetch_info, sym): sym for sym in symbols}
    for fut in concurrent.futures.as_completed(futures):
        res = fut.result()
        if res:
            results[res['symbol']] = res
        count += 1
        if count % 100 == 0:
            print(f"Processed {count}/{len(symbols)}")

for idx_key in data:
    for item in data[idx_key]['constituents']:
        sym = item['symbol']
        if sym in results:
            for k in keys_to_add:
                item[k] = results[sym].get(k)

with open('static/index_data.json', 'w') as f:
    json.dump(data, f)
print("Updated index_data.json successfully.")
