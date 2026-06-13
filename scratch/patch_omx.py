with open('scratch/compile_international.py', 'r') as f:
    content = f.read()

old_omx = '''        omx_tickers = omx_df['Ticker'].astype(str) + '.ST'
        omx_tickers = omx_tickers.tolist()'''

new_omx = '''        omx_tickers = [str(t).replace(' ', '-').replace('.ST', '') + '.ST' for t in omx_df['Ticker'].astype(str)]'''

content = content.replace(old_omx, new_omx)

with open('scratch/compile_international.py', 'w') as f:
    f.write(content)
print('compile_international.py patched!')
