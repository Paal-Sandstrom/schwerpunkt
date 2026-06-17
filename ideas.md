# Schwerpunkt Terminal: Roadmap & Ideas

Here is a brainstorming list of potential features and technical improvements we could tackle next. 

## 🚀 Epic Features to Add

1. **Portfolio & Paper Trading Simulator**
   - Add terminal commands to `buy [ticker] [shares]` and `sell [ticker]`.
   - Create a new "Portfolio" tab that tracks your PnL, portfolio allocation (pie chart), and total return using the live data we are already fetching.

2. **Live News Wire**
   - Integrate an RSS feed (like Yahoo Finance news, Reuters, or Bloomberg) to display a scrolling "News Wire" at the very bottom of the screen.
   - Add a terminal command `news [ticker]` to fetch the top 3 latest headlines for a specific stock directly in the console.

3. **Technical Indicators on Charts**
   - Expand our Chart.js implementation to allow overlaying technical indicators (50-day / 200-day Simple Moving Averages, RSI, MACD).
   - Controllable via the terminal: e.g., `chart AAPL --sma 50`.

4. **ASCII / Console Charts**
   - Bring true retro flair to the terminal by allowing users to type `ascii [ticker]` to render a pure-text candlestick chart directly within the terminal output box, completely bypassing the GUI.

5. **Advanced Stock Screener**
   - Add a command-line screener. Example: `screen --pe < 15 --cap > 10B --sector Tech` to return a list of matching stocks from the S&P 500 or Russell 3000 indices.

6. **Options Data & Insider Trading**
   - Fetch and display the options chain (puts/calls) or unusual options volume.
   - Display a tracker for recent CEO/Insider buying and selling activity.

## 🛠️ Things to Fix / Technical Debt

1. **Robust Database / Persistent Caching**
   - *Current state:* We are relying heavily on in-memory caching (`app_cache`) and `localStorage` for notes/folders. If the server restarts or you clear your browser data, things are lost.
   - *Fix:* Migrate to a lightweight persistent database like SQLite to permanently store the user's research dossier, terminal settings, and heavily cache the `yfinance` data.

2. **yFinance Rate Limit Hardening**
   - *Current state:* Yahoo Finance can occasionally rate-limit our IP if we fetch too much data at once.
   - *Fix:* Implement an exponential backoff retry system, rotate user-agents dynamically, or add a secondary fallback API (like AlphaVantage) to ensure the app never goes down.

3. **Mobile Layout Polish**
   - *Current state:* The app is responsive, but complex data tables and charts can still feel a bit cramped on very small screens (like an iPhone SE).
   - *Fix:* Overhaul the mobile CSS to transform tables into card-based layouts on small screens, ensuring the retro aesthetic is preserved flawlessly on mobile.

4. **WebSocket Live Streaming**
   - *Current state:* We fetch prices on page load or via explicit commands.
   - *Fix:* Establish a WebSocket connection to stream price ticks in real-time. The terminal background could subtly flash green/red as prices update live!
