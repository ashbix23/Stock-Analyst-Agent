# Stock Analyst Agent

An autonomous multi-tool AI agent that analyzes any publicly traded stock and produces a structured equity research report. Given a ticker symbol, the agent calls four data sources in parallel — live price data, recent news, financial statements, and SEC filings — then synthesizes everything into a professional analyst-grade report using Claude.

Built to demonstrate multi-tool agentic AI engineering with a fintech domain focus.

---

## Report Sections

Every generated report includes:

- **Executive Summary** — key takeaway and overall signal (bullish / bearish / mixed)
- **Price & Technicals** — current price, 5-day OHLCV, moving averages, 52-week range, analyst target and upside
- **Financial Health** — revenue trend, margins, net income, EPS, balance sheet highlights
- **Valuation** — TTM P/E, forward P/E, market cap, fundamental justification
- **News & Sentiment** — top 5 recent headlines, dominant sentiment tone, material events
- **SEC Filings** — most recent 10-K and 10-Q with EDGAR links
- **Key Risks** — 3–5 data-grounded risks
- **Bull vs. Bear Case** — specific arguments on both sides
- **Analyst Verdict** — a clear, data-backed position

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent & LLM | Anthropic API (`claude-sonnet-4-6`) — native tool calling |
| Market data | `yfinance` — price, metrics, financials |
| News | NewsAPI — recent headlines and sentiment |
| SEC filings | SEC EDGAR public API — 10-K / 10-Q metadata |
| CLI | `rich` — formatted terminal output |
| Tables | `tabulate` — clean data formatting |

---

## Project Structure

```
stock-analyst-agent/
├── main.py                  # CLI entrypoint
├── agent.py                 # Tool-calling loop
├── tools/
│   ├── __init__.py
│   ├── price_data.py        # yfinance price + technicals
│   ├── news.py              # NewsAPI headlines
│   ├── financials.py        # yfinance income + balance sheet
│   └── filings.py           # SEC EDGAR 10-K / 10-Q
├── prompts/
│   ├── __init__.py
│   ├── system.py            # Agent system prompt
│   └── report.py            # Report generation prompt
├── output/                  # Generated reports
├── requirements.txt
└── .env.example
```

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/ashbix23/Stock-Analyst-Agent
cd Stock-Analyst-Agent
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
NEWS_API_KEY=your_news_api_key_here
```

| Key | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org) — free tier (100 req/day) |

SEC EDGAR and yfinance require no API keys.

**4. Run**
```bash
python main.py AAPL
```

Or pass the ticker as an argument:
```bash
python main.py MSFT
python main.py TSLA
python main.py NVDA
```

Reports are saved to `output/report_{TICKER}_{DATE}.md`.

---

## Example Tickers

```bash
python main.py AAPL    # Apple
python main.py MSFT    # Microsoft
python main.py NVDA    # NVIDIA
python main.py TSLA    # Tesla
python main.py JPM     # JPMorgan Chase
python main.py GS      # Goldman Sachs
```


