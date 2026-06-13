import os
import json
import time
import requests
import io
import pandas as pd
import concurrent.futures
import yfinance as yf
import numpy as np
import datetime

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

def get_usd_rate(currency):
    try:
        t = yf.Ticker(f"{currency}USD=X")
        return float(t.history(period="1d")['Close'].iloc[-1])
    except:
        return 1.0

def main():
    print("Loading existing index_data.json...")
    input_path = os.path.join("static", "index_data.json")
    if os.path.exists(input_path):
        with open(input_path, 'r') as f:
            output_data = json.load(f)
    else:
        output_data = {}

    print("Fetching Nikkei 225 (from topforeignstocks or fallback to static mapping if needed)...")
    # Wikipedia doesn't have a clean table, let's just pull it from a known Github gist or URL.
    # To keep it simple, we can fetch from a generic list or just use top 30 as a demo if we can't find 225.
    # Wait, Wikipedia Nikkei 225 page has "Nikkei 225 companies of Japan" navigational template!
    # Let's scrape all hrefs inside `class="navbox"` where title is a company.
    # Actually, pulling from topforeignstocks CSV is reliable.
    try:
        res = requests.get('https://topforeignstocks.com/indices/the-components-of-the-nikkei-225-index/', headers=headers)
        tables = pd.read_html(io.StringIO(res.text))
        for t in tables:
            if 'Code' in t.columns:
                df = t
                break
        nikkei_tickers = df['Code'].astype(str).tolist()
    except Exception as e:
        print("Nikkei Fetch Error", e)
        nikkei_tickers = ['7203.T', '6758.T', '9984.T', '6861.T', '9432.T', '8306.T', '8035.T', '6098.T', '6981.T', '7974.T']

    # Ensure suffix
    nikkei_tickers = [str(t).replace('.T', '') + '.T' for t in nikkei_tickers if str(t).strip()]
    print(f"Loaded {len(nikkei_tickers)} Nikkei 225 tickers.")

    print("Fetching OMXS30 from Wikipedia...")
    try:
        res = requests.get('https://en.wikipedia.org/wiki/OMX_Stockholm_30', headers=headers)
        tables = pd.read_html(io.StringIO(res.text))
        for t in tables:
            if 'Ticker' in t.columns:
                omx_df = t
                break
        omx_tickers = [str(t).replace(' ', '-').replace('.ST', '') + '.ST' for t in omx_df['Ticker'].astype(str)]
        print(f"Loaded {len(omx_tickers)} OMXS30 tickers.")
    except Exception as e:
        print("Fallback for OMXS30")
        omx_tickers = ['VOLV-B.ST', 'ERIC-B.ST', 'ATCO-A.ST', 'INVE-B.ST', 'SEB-A.ST', 'ASSA-B.ST', 'HM-B.ST']

    unique_tickers = set(nikkei_tickers + omx_tickers)
    print(f"Fetching data for {len(unique_tickers)} international stocks...")

    # Fetch info and PE
    results = []
    def fetch_data(symbol):
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            currency = info.get('currency', 'USD')
            rate = get_usd_rate(currency) if currency != 'USD' else 1.0
            
            pe = info.get('trailingPE', 20.0)
            mc = info.get('marketCap', 0) * rate
            name = info.get('shortName', symbol)
            sector = info.get('sector', 'Other')
            return {
                'symbol': symbol,
                'name': name,
                'market_cap': int(mc),
                'pe_ratio': round(pe, 2),
                'sector': sector
            }
        except Exception:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        stock_results = list(executor.map(fetch_data, list(unique_tickers)))

    stock_map = {r['symbol']: r for r in stock_results if r}

    nikkei_data = [stock_map[t] for t in nikkei_tickers if t in stock_map]
    nikkei_data.sort(key=lambda x: x['market_cap'], reverse=True)
    
    omx_data = [stock_map[t] for t in omx_tickers if t in stock_map]
    omx_data.sort(key=lambda x: x['market_cap'], reverse=True)

    print("Fetching index historical growth...")
    yearly_growth = {}
    for idx_id, symbol in {'nikkei225': '^N225', 'omxs30': '^OMX'}.items():
        try:
            hist = yf.Ticker(symbol).history(period="12y")
            if not hist.empty:
                yearly_closes = hist['Close'].groupby(hist.index.year).last()
                returns = (yearly_closes.pct_change() * 100).dropna()
                yearly_growth[idx_id] = [{'year': int(yr), 'growth': round(val, 2)} for yr, val in returns.items()]
            else:
                yearly_growth[idx_id] = []
        except:
            yearly_growth[idx_id] = []

    output_data['nikkei225'] = {
        'constituents': nikkei_data,
        'growth': yearly_growth.get('nikkei225', [])
    }
    
    output_data['omxs30'] = {
        'constituents': omx_data,
        'growth': yearly_growth.get('omxs30', [])
    }

    with open(input_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"SUCCESS! Wrote {len(nikkei_data)} Nikkei and {len(omx_data)} OMXS30 stocks to {input_path}")

if __name__ == '__main__':
    main()
