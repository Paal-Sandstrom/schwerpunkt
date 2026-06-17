# Walkthrough: Mobile Layout & Advanced Screener

We just shipped a massive update to Schwerpunkt! Here is a summary of the new features and fixes you'll see in this deployment:

## 📱 Mobile Responsiveness Overhaul
The app has been completely optimized for smaller screens:
- **Vertical Stacking:** The main dashboard panels and sidebars now stack vertically on laptops and phones, preventing the UI from feeling claustrophobic.
- **Scrollable Data Tables:** If a financial table is too wide for your phone screen, you can now seamlessly swipe/scroll horizontally inside the table without dragging the whole page off-screen.
- **Header Repositioning:** The top navigation bar now wraps its links dynamically based on your screen width.

## 🔎 Advanced Local Screener
I've successfully implemented your list of `yfinance` filter requirements! To make this screener lightning-fast, I wrote a background script that fetched all 18 of your requested metrics (P/E, ROE, Current Ratio, Dividend Yield, etc.) for all ~4,000 stocks in our index universe and compiled them into our local `index_data.json` database.

**How to use it:**
1. Click the new **Screener** link in the top navigation bar.
2. Select your filters using the dropdown menus (e.g., *Market Cap: Large*, *Sector: Technology*, *Trailing P/E: < 20*, *ROE: > 15%*).
3. Click **RUN SCREENER**.
4. The JavaScript engine will instantaneously filter the 4,000-stock database in your browser and render a classic retro data table containing the matching stocks, sorted by Market Cap.
5. You can click on any symbol in the resulting table to jump straight to its deep-dive page and run a DCF valuation!

> [!TIP]
> Because the screener dataset is loaded directly into your browser memory when you open the tab, running screens is completely instantaneous and doesn't ping Yahoo Finance! You will never hit rate limits while testing different filter combinations.
