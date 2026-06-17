# Implementation Plan: Mobile Optimization & Advanced Screener

## 1. Mobile Layout Refinement
To ensure the app looks stellar on smaller screens (like laptops and phones), we'll implement responsive CSS media queries:
- **Responsive Stacking:** The main content and sidebars (currently side-by-side) will stack vertically on screens under 768px.
- **Scrollable Data Tables:** Complex financial tables will be wrapped in horizontal scroll containers (`overflow-x: auto`) to prevent the page layout from breaking or stretching off-screen.
- **Terminal Handling:** We will adjust the floating terminal bounds logic to ensure it behaves cleanly on mobile devices without overlapping critical data.

## 2. Advanced Stock Screener Tab
We will build a new **Screener** tab accessible from the main navigation menu. Because calculating metrics like Free Cash Flow Growth and P/E ratios for 5,000+ global stocks in real-time is too resource-intensive for a local script, we will build a stealthy backend proxy that queries industry-standard financial databases (like Finviz) and pipes the parsed results directly into our retro UI.

**Features of the Screener:**
- **Metric Dropdowns:** Users can select filters such as:
  - **Market Cap:** (Mega, Large, Mid, Small)
  - **Valuation:** (P/E Ratio, Forward P/E)
  - **Growth:** (EPS Growth YoY, Sales Growth, FCF metrics)
  - **Sector/Industry:** (Tech, Healthcare, Financials, etc.)
  - **Geography:** (US vs International)
- **Live Results Table:** A dynamically updating table showing tickers, names, market caps, P/E ratios, and daily changes for the stocks that pass the screen.
- **One-Click Analysis:** Clicking any ticker in the screener results will instantly load its DCF valuation and deep-dive financial metrics in the main app.

> [!IMPORTANT]
> **User Review Required**
> Finviz does not explicitly track "Free Cash Flow Growth" as a single filterable parameter. Instead, it tracks **EPS Growth**, **Sales Growth**, and **Price-to-Free-Cash-Flow (P/FCF)**. I plan to include P/FCF and EPS/Sales growth as the primary proxies for your growth/FCF requirements. Does this sound good to you?

## Verification Plan
1. Test the new media queries by resizing the browser window to simulate an iPhone SE and checking table scrollability.
2. Run a complex screen (e.g., Tech stocks > $10B Market Cap with P/E < 15) and verify the backend correctly parses and returns the matching stocks.
