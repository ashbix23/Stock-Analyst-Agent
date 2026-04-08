import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule

from agent import run_agent

load_dotenv()
console = Console()


def validate_env() -> bool:
    """Check required environment variables are set."""
    missing = []

    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.getenv("NEWS_API_KEY"):
        console.print("[yellow]Warning: NEWS_API_KEY not set — news section will be skipped.[/yellow]")

    if missing:
        console.print(f"[red]Error: Missing required environment variables: {', '.join(missing)}[/red]")
        console.print("Copy .env.example to .env and fill in your keys.")
        return False

    return True


def save_report(ticker: str, report: str) -> Path:
    """Save the report to the output directory."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = output_dir / f"report_{ticker.upper()}_{date_str}.md"

    with open(filename, "w") as f:
        f.write(report)

    return filename


def main():
    console.print(Panel.fit(
        "[bold purple]Stock Market Analyst Agent[/bold purple]\n"
        "[dim]Powered by Claude + yfinance + NewsAPI + SEC EDGAR[/dim]",
        border_style="purple",
    ))

    # Get ticker from CLI arg or prompt
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper().strip()
    else:
        ticker = console.input("\n[bold]Enter ticker symbol[/bold] (e.g. AAPL, MSFT, TSLA): ").upper().strip()

    if not ticker:
        console.print("[red]No ticker provided. Exiting.[/red]")
        sys.exit(1)

    if not validate_env():
        sys.exit(1)

    console.print(Rule(style="purple"))

    # Run the agent
    try:
        report = run_agent(ticker)
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis cancelled.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Agent error: {e}[/red]")
        raise

    # Display the report
    console.print(Rule(style="purple"))
    console.print("\n[bold green]Report generated:[/bold green]\n")
    console.print(Markdown(report))

    # Save to file
    saved_path = save_report(ticker, report)
    console.print(Rule(style="purple"))
    console.print(f"\n[bold]Report saved to:[/bold] [cyan]{saved_path}[/cyan]")
    console.print("\n[dim]Disclaimer: This report is for informational purposes only. Not financial advice.[/dim]\n")


if __name__ == "__main__":
    main()
