# Schwerpunkt

Schwerpunkt is an early 2000s Web 2.0 styled stock market research terminal. Built with Python, Flask, and SQLite, it offers a robust financial data dashboard combined with personal research organization tools.

## Features
- **Retro Terminal Interface:** A powerful CLI-like interface directly in the browser to query live stock data, create research folders, and take notes.
- **Financial Dashboards:** Live SPDR sector heatmap, market indices, top market movers, and a macro economic calendar.
- **Detailed Ticker Data:** Real-time stock prices, historical charts, and full financial statements (Income, Balance Sheet, Cash Flow) fetched via `yfinance`.
- **DCF Valuation Tool:** Interactive Discounted Cash Flow calculator with editable inputs for growth rates and base FCF.
- **Research Folders:** Organize your investment thesis with custom folders and note-taking.

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd schwerpunkt
```

2. Install the requirements:
```bash
pip install -r requirements.txt
```

3. Initialize the local database:
```bash
python db.py
```

4. Run the Flask application:
```bash
python app.py
# Or run with flask directly:
flask run
```

## Tech Stack
- **Backend:** Python, Flask, SQLite3
- **Data Source:** `yfinance`
- **Frontend:** HTML, Vanilla CSS (Web 2.0 aesthetic), JavaScript, Chart.js
