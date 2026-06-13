with open('scratch/compile_international.py', 'r') as f:
    content = f.read()

old_nikkei = '''    try:
        res = requests.get('https://raw.githubusercontent.com/FEC1/Stock-Market-Data/master/Indices/Nikkei_225_components.csv')
        # If it fails, we will generate a dummy list of top 10 Japanese stocks.
        if res.status_code == 200:
            df = pd.read_csv(io.StringIO(res.text))
            if 'Ticker' in df.columns:
                nikkei_tickers = df['Ticker'].astype(str).tolist()
            else:
                nikkei_tickers = [line.split(',')[0] for line in res.text.split('\\n')[1:] if line.strip()]
        else:
            raise Exception("URL failed")
    except:
        # Fallback to hardcoded top Japanese stocks to ensure it works
        nikkei_tickers = ['7203.T', '6758.T', '9984.T', '6861.T', '9432.T', '8306.T', '8035.T', '6098.T', '6981.T', '7974.T']'''

new_nikkei = '''    try:
        res = requests.get('https://topforeignstocks.com/indices/the-components-of-the-nikkei-225-index/', headers=headers)
        tables = pd.read_html(io.StringIO(res.text))
        for t in tables:
            if 'Code' in t.columns:
                df = t
                break
        nikkei_tickers = df['Code'].astype(str).tolist()
    except Exception as e:
        print("Nikkei Fetch Error", e)
        nikkei_tickers = ['7203.T', '6758.T', '9984.T', '6861.T', '9432.T', '8306.T', '8035.T', '6098.T', '6981.T', '7974.T']'''

content = content.replace(old_nikkei, new_nikkei)

with open('scratch/compile_international.py', 'w') as f:
    f.write(content)
