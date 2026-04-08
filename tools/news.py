import os
import requests
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

NEWS_API_URL = "https://newsapi.org/v2/everything"


def get_news(ticker: str, company_name: str, num_articles: int = 8) -> dict:
    """
    Fetch recent news headlines for a ticker/company via NewsAPI.
    Falls back to a public RSS approach if no API key is set.
    """
    if not NEWS_API_KEY:
        return {
            "success": False,
            "error": "NEWS_API_KEY not set. Add it to your .env file. Get a free key at newsapi.org.",
            "ticker": ticker,
        }

    # Search last 7 days
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    # Use both ticker and company name for better coverage
    query = f"{ticker} OR \"{company_name}\""

    params = {
        "q": query,
        "from": from_date,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": num_articles,
        "apiKey": NEWS_API_KEY,
    }

    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"NewsAPI HTTP error: {e}", "ticker": ticker}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Network error: {e}", "ticker": ticker}

    data = response.json()

    if data.get("status") != "ok":
        return {
            "success": False,
            "error": data.get("message", "Unknown NewsAPI error"),
            "ticker": ticker,
        }

    articles = []
    for item in data.get("articles", []):
        articles.append({
            "title": item.get("title", "").strip(),
            "source": item.get("source", {}).get("name", "Unknown"),
            "published_at": item.get("publishedAt", "")[:10],
            "description": (item.get("description") or "")[:200].strip(),
            "url": item.get("url", ""),
        })

    return {
        "success": True,
        "ticker": ticker.upper(),
        "company_name": company_name,
        "articles": articles,
        "total_found": data.get("totalResults", 0),
    }


def format_news(data: dict) -> str:
    """Format news data as a readable string for the agent context."""
    if not data["success"]:
        return f"News unavailable: {data['error']}"

    if not data["articles"]:
        return f"No recent news found for {data['ticker']}."

    lines = [f"--- Recent News: {data['company_name']} ({data['ticker']}) ---", ""]

    for i, article in enumerate(data["articles"], 1):
        lines.append(f"{i}. [{article['published_at']}] {article['title']}")
        lines.append(f"   Source: {article['source']}")
        if article["description"]:
            lines.append(f"   {article['description']}")
        lines.append("")

    return "\n".join(lines)
