import requests


EDGAR_BASE = "https://data.sec.gov/submissions"
EDGAR_HEADERS = {
    "User-Agent": "stock-analyst-agent contact@example.com"  # EDGAR requires a User-Agent
}


def get_filings(ticker: str) -> dict:
    """
    Fetch the most recent 10-K and 10-Q filings from SEC EDGAR.
    No API key required — EDGAR is a free public API.
    """
    try:
        # Step 1: Resolve ticker to CIK number
        cik = _get_cik(ticker)
        if not cik:
            return {
                "success": False,
                "error": f"Could not resolve CIK for ticker {ticker}. Company may not be SEC-registered.",
                "ticker": ticker,
            }

        # Step 2: Fetch submission history
        url = f"{EDGAR_BASE}/CIK{cik}.json"
        response = requests.get(url, headers=EDGAR_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accessions = filings.get("accessionNumber", [])
        descriptions = filings.get("primaryDocument", [])

        # Step 3: Pull the most recent 10-K and 10-Q
        results = []
        seen_types = set()

        for form, date, accession, doc in zip(forms, dates, accessions, descriptions):
            if form in ("10-K", "10-Q") and form not in seen_types:
                accession_clean = accession.replace("-", "")
                filing_url = (
                    f"https://www.sec.gov/Archives/edgar/full-index/"
                    f"{date[:4]}/QTR{_quarter(date)}/{accession_clean}-index.htm"
                )
                viewer_url = (
                    f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
                    f"&CIK={cik}&type={form}&dateb=&owner=include&count=5"
                )
                results.append({
                    "form_type": form,
                    "filing_date": date,
                    "accession_number": accession,
                    "viewer_url": viewer_url,
                })
                seen_types.add(form)

            if len(seen_types) == 2:
                break

        return {
            "success": True,
            "ticker": ticker.upper(),
            "cik": cik,
            "company_name": data.get("name", ticker),
            "filings": results,
        }

    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"EDGAR HTTP error: {e}", "ticker": ticker}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Network error: {e}", "ticker": ticker}
    except Exception as e:
        return {"success": False, "error": str(e), "ticker": ticker}


def _get_cik(ticker: str) -> str | None:
    """Resolve a ticker symbol to an SEC CIK number."""
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers=EDGAR_HEADERS, timeout=10)
        response.raise_for_status()
        tickers_data = response.json()

        for entry in tickers_data.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                return str(entry["cik_str"]).zfill(10)
        return None
    except Exception:
        return None


def _quarter(date_str: str) -> int:
    """Return the fiscal quarter (1-4) for a given date string YYYY-MM-DD."""
    month = int(date_str[5:7])
    return (month - 1) // 3 + 1


def format_filings(data: dict) -> str:
    """Format filings data as a readable string for the agent context."""
    if not data["success"]:
        return f"SEC filings unavailable: {data['error']}"

    if not data["filings"]:
        return f"No recent 10-K or 10-Q filings found for {data['ticker']}."

    lines = [
        f"--- SEC Filings: {data['company_name']} ({data['ticker']}) ---",
        f"CIK: {data['cik']}",
        "",
    ]

    for filing in data["filings"]:
        lines.append(f"Form {filing['form_type']} — Filed: {filing['filing_date']}")
        lines.append(f"Accession: {filing['accession_number']}")
        lines.append(f"View on EDGAR: {filing['viewer_url']}")
        lines.append("")

    return "\n".join(lines)
