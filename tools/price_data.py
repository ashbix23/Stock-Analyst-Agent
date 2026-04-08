import yfinance as yf
from tabulate import tabulate


def get_price_data(ticker: str) -> dict:
    """
    Fetch current price, OHLCV, and key metrics for a ticker.
    Returns a structured dict the agent can read.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Recent OHLCV (last 5 trading days)
        hist = stock.history(period="5d")
        if hist.empty:
            return {"success": False, "error": f"No price data found for {ticker}"}

        recent_prices = []
        for date, row in hist.iterrows():
            recent_prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })

        # Key metrics
        metrics = {
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "day_high": info.get("dayHigh"),
            "day_low": info.get("dayLow"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "eps": info.get("trailingEps"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "avg_volume": info.get("averageVolume"),
            "fifty_day_avg": info.get("fiftyDayAverage"),
            "two_hundred_day_avg": info.get("twoHundredDayAverage"),
            "analyst_target_price": info.get("targetMeanPrice"),
            "recommendation": info.get("recommendationKey"),
        }

        # Clean out None values
        metrics = {k: v for k, v in metrics.items() if v is not None}

        return {
            "success": True,
            "ticker": ticker.upper(),
            "company_name": info.get("longName", ticker),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "metrics": metrics,
            "recent_prices": recent_prices,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def format_price_data(data: dict) -> str:
    """Format price data as a readable string for the agent context."""
    if not data["success"]:
        return f"Price data unavailable: {data['error']}"

    lines = [
        f"Company: {data['company_name']} ({data['ticker']})",
        f"Sector: {data['sector']} | Industry: {data['industry']}",
        "",
        "--- Key Metrics ---",
    ]

    m = data["metrics"]
    metric_rows = []
    if "current_price" in m:
        metric_rows.append(["Current Price", f"${m['current_price']:,.2f}"])
    if "previous_close" in m:
        metric_rows.append(["Previous Close", f"${m['previous_close']:,.2f}"])
    if "fifty_two_week_high" in m and "fifty_two_week_low" in m:
        metric_rows.append(["52-Week Range", f"${m['fifty_two_week_low']:,.2f} - ${m['fifty_two_week_high']:,.2f}"])
    if "market_cap" in m:
        metric_rows.append(["Market Cap", f"${m['market_cap']:,.0f}"])
    if "pe_ratio" in m:
        metric_rows.append(["P/E Ratio (TTM)", f"{m['pe_ratio']:.2f}"])
    if "forward_pe" in m:
        metric_rows.append(["Forward P/E", f"{m['forward_pe']:.2f}"])
    if "eps" in m:
        metric_rows.append(["EPS (TTM)", f"${m['eps']:.2f}"])
    if "beta" in m:
        metric_rows.append(["Beta", f"{m['beta']:.2f}"])
    if "fifty_day_avg" in m:
        metric_rows.append(["50-Day Avg", f"${m['fifty_day_avg']:,.2f}"])
    if "two_hundred_day_avg" in m:
        metric_rows.append(["200-Day Avg", f"${m['two_hundred_day_avg']:,.2f}"])
    if "analyst_target_price" in m:
        metric_rows.append(["Analyst Target", f"${m['analyst_target_price']:,.2f}"])
    if "recommendation" in m:
        metric_rows.append(["Analyst Rating", m["recommendation"].upper()])

    lines.append(tabulate(metric_rows, tablefmt="simple"))

    lines += ["", "--- Recent Price History (5 days) ---"]
    price_rows = [
        [p["date"], f"${p['open']:.2f}", f"${p['high']:.2f}",
         f"${p['low']:.2f}", f"${p['close']:.2f}", f"{p['volume']:,}"]
        for p in data["recent_prices"]
    ]
    lines.append(tabulate(price_rows, headers=["Date", "Open", "High", "Low", "Close", "Volume"], tablefmt="simple"))

    return "\n".join(lines)
