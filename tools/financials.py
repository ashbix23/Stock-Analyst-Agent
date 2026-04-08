import yfinance as yf
from tabulate import tabulate


def get_financials(ticker: str) -> dict:
    """
    Fetch income statement and balance sheet data via yfinance.
    Returns annual figures for the last 2 years.
    """
    try:
        stock = yf.Ticker(ticker)

        # Income statement (annual)
        income_stmt = stock.income_stmt
        balance_sheet = stock.balance_sheet

        if income_stmt is None or income_stmt.empty:
            return {"success": False, "error": f"No financial data found for {ticker}"}

        # Pull the most recent 2 years
        income_cols = income_stmt.columns[:2]
        balance_cols = balance_sheet.columns[:2] if not balance_sheet.empty else []

        # Key income statement rows
        income_rows_of_interest = [
            "Total Revenue",
            "Gross Profit",
            "Operating Income",
            "EBITDA",
            "Net Income",
            "Basic EPS",
            "Diluted EPS",
        ]

        # Key balance sheet rows
        balance_rows_of_interest = [
            "Total Assets",
            "Total Liabilities Net Minority Interest",
            "Stockholders Equity",
            "Cash And Cash Equivalents",
            "Total Debt",
            "Net Debt",
        ]

        def extract_rows(df, row_names, cols):
            result = {}
            for row in row_names:
                if row in df.index:
                    result[row] = {
                        col.strftime("%Y"): df.loc[row, col]
                        for col in cols
                        if col in df.columns
                    }
            return result

        income_data = extract_rows(income_stmt, income_rows_of_interest, income_cols)
        balance_data = extract_rows(
            balance_sheet, balance_rows_of_interest, balance_cols
        ) if not balance_sheet.empty else {}

        return {
            "success": True,
            "ticker": ticker.upper(),
            "income_statement": income_data,
            "balance_sheet": balance_data,
            "years": [col.strftime("%Y") for col in income_cols],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def _fmt(value) -> str:
    """Format a financial value — billions if large, otherwise millions."""
    try:
        v = float(value)
        if abs(v) >= 1e9:
            return f"${v / 1e9:.2f}B"
        elif abs(v) >= 1e6:
            return f"${v / 1e6:.2f}M"
        else:
            return f"${v:.2f}"
    except (TypeError, ValueError):
        return "N/A"


def format_financials(data: dict) -> str:
    """Format financials as a readable string for the agent context."""
    if not data["success"]:
        return f"Financial data unavailable: {data['error']}"

    years = data["years"]
    lines = [f"--- Financials: {data['ticker']} (Annual) ---", ""]

    # Income statement table
    lines.append("Income Statement:")
    income_rows = []
    for label, year_vals in data["income_statement"].items():
        row = [label] + [_fmt(year_vals.get(y, "N/A")) for y in years]
        income_rows.append(row)

    if income_rows:
        lines.append(
            tabulate(income_rows, headers=["Metric"] + years, tablefmt="simple")
        )
    else:
        lines.append("No income statement data available.")

    lines.append("")

    # Balance sheet table
    lines.append("Balance Sheet:")
    balance_rows = []
    for label, year_vals in data["balance_sheet"].items():
        row = [label] + [_fmt(year_vals.get(y, "N/A")) for y in years]
        balance_rows.append(row)

    if balance_rows:
        lines.append(
            tabulate(balance_rows, headers=["Metric"] + years, tablefmt="simple")
        )
    else:
        lines.append("No balance sheet data available.")

    return "\n".join(lines)
