import json
import os
from anthropic import Anthropic
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

from tools import (
    get_price_data, format_price_data,
    get_news, format_news,
    get_financials, format_financials,
    get_filings, format_filings,
)
from prompts import SYSTEM_PROMPT, REPORT_PROMPT

import os
from dotenv import load_dotenv
load_dotenv()

client = Anthropic()
console = Console()

# Tool definitions for the Anthropic API
TOOLS = [
    {
        "name": "get_price_data",
        "description": "Fetch current price, key metrics (P/E, market cap, beta, 52-week range, analyst target), and 5-day OHLCV history for a stock ticker using yfinance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol, e.g. AAPL, MSFT, TSLA",
                }
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_news",
        "description": "Fetch the most recent news headlines and descriptions for a stock ticker via NewsAPI.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol, e.g. AAPL",
                },
                "company_name": {
                    "type": "string",
                    "description": "The full company name, e.g. Apple Inc. Used to improve news search coverage.",
                },
            },
            "required": ["ticker", "company_name"],
        },
    },
    {
        "name": "get_financials",
        "description": "Fetch annual income statement and balance sheet data for a stock ticker using yfinance. Returns revenue, gross profit, net income, EPS, total assets, debt, and equity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol, e.g. AAPL",
                }
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_filings",
        "description": "Fetch the most recent 10-K and 10-Q SEC filings for a company from EDGAR. No API key required.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol, e.g. AAPL",
                }
            },
            "required": ["ticker"],
        },
    },
]


def run_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call and return formatted string output."""
    if tool_name == "get_price_data":
        data = get_price_data(tool_input["ticker"])
        return format_price_data(data)

    elif tool_name == "get_news":
        data = get_news(tool_input["ticker"], tool_input["company_name"])
        return format_news(data)

    elif tool_name == "get_financials":
        data = get_financials(tool_input["ticker"])
        return format_financials(data)

    elif tool_name == "get_filings":
        data = get_filings(tool_input["ticker"])
        return format_filings(data)

    else:
        return f"Unknown tool: {tool_name}"


def run_agent(ticker: str) -> str:
    """
    Run the full analyst agent loop for a given ticker.
    Returns the final Markdown report as a string.
    """
    messages = [
        {
            "role": "user",
            "content": f"Please analyze the stock {ticker.upper()} and produce a full equity research report.",
        }
    ]

    console.print(f"\n[bold purple]Starting analysis for {ticker.upper()}...[/bold purple]\n")

    # Agentic loop
    while True:
        with Live(Spinner("dots", text="Thinking..."), console=console, transient=True):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

        # Check stop reason
        if response.stop_reason == "end_turn":
            # Extract final text response
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "No report generated."

        if response.stop_reason != "tool_use":
            console.print(f"[red]Unexpected stop reason: {response.stop_reason}[/red]")
            break

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                console.print(f"[cyan]  → Calling tool:[/cyan] [bold]{block.name}[/bold] with {block.input}")

                with Live(Spinner("dots", text=f"Running {block.name}..."), console=console, transient=True):
                    result = run_tool(block.name, block.input)

                console.print(f"[green]  ✓ {block.name} complete[/green]")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        # Append assistant response and tool results to message history
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        # Inject the report prompt after all tools have been called
        tools_called = {
            block.name for block in response.content if block.type == "tool_use"
        }
        required_tools = {"get_price_data", "get_news", "get_financials", "get_filings"}

        # Check if all required tools have been called across the full message history
        all_tools_called = set()
        for msg in messages:
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if hasattr(block, "type") and block.type == "tool_use":
                        all_tools_called.add(block.name)
                    elif isinstance(block, dict) and block.get("type") == "tool_use":
                        all_tools_called.add(block.get("name"))

        if required_tools.issubset(all_tools_called):
            # All tools done — inject the report generation instruction
            messages.append({
                "role": "user",
                "content": REPORT_PROMPT,
            })

    return "Agent loop ended unexpectedly."
