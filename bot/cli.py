"""
cli.py - Enhanced CLI for the Binance Futures Testnet trading bot.
Features: rich menus (questionary), live price fetch, all order types,
          account balance view, and full colour output via rich.

Usage:
    python cli.py                        # interactive menu
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 50000
    python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 60000
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import questionary
from questionary import Style as QStyle
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

from client import BinanceClient
from orders import place_order
from validators import VALID_SYMBOLS, VALID_SIDES, VALID_ORDER_TYPES, LIMIT_ORDER_TYPES, STOP_ORDER_TYPES
from logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
console = Console()

# ── Questionary colour theme ─────────────────────────────────────────────────
Q_STYLE = QStyle([
    ("qmark",        "fg:#00d7ff bold"),
    ("question",     "bold"),
    ("answer",       "fg:#00ff87 bold"),
    ("pointer",      "fg:#00d7ff bold"),
    ("highlighted",  "fg:#00d7ff bold"),
    ("selected",     "fg:#00ff87"),
    ("separator",    "fg:#6c6c6c"),
    ("instruction",  "fg:#6c6c6c"),
])

ORDER_TYPE_DESCRIPTIONS = {
    "MARKET":              "MARKET          — Execute immediately at current price",
    "LIMIT":               "LIMIT           — Execute at a specific price or better",
    "STOP_MARKET":         "STOP_MARKET     — Trigger a market order at stop price",
    "STOP_LIMIT":          "STOP_LIMIT      — Trigger a limit order at stop price",
    "TAKE_PROFIT_MARKET":  "TAKE_PROFIT_MARKET — Close at profit target (market)",
    "TAKE_PROFIT":         "TAKE_PROFIT     — Close at profit target (limit)",
}

BANNER = Panel(
    Text.from_markup(
        "[bold cyan]Binance Futures Testnet[/] [dim]|[/] [bold]Trading Bot[/]\n"
        "[dim]https://testnet.binancefuture.com[/]"
    ),
    box=box.DOUBLE_EDGE,
    border_style="cyan",
    padding=(0, 2),
)


# ── Credentials ──────────────────────────────────────────────────────────────

def get_credentials() -> tuple[str, str]:
    api_key    = os.getenv("BINANCE_TESTNET_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_TESTNET_API_SECRET", "").strip()
    if not api_key or not api_secret:
        console.print("\n[bold red][!] API credentials not set.[/]\n")
        console.print("Export before running:")
        console.print("  [cyan]export BINANCE_TESTNET_API_KEY='your_key'[/]")
        console.print("  [cyan]export BINANCE_TESTNET_API_SECRET='your_secret'[/]\n")
        sys.exit(1)
    return api_key, api_secret


# ── Live price helper ─────────────────────────────────────────────────────────

def fetch_price(client: BinanceClient, symbol: str) -> str:
    try:
        data = client.get_symbol_price(symbol)
        return data.get("price", "—")
    except Exception:
        return "unavailable"


# ── Account balance view ──────────────────────────────────────────────────────

def show_balance(client: BinanceClient):
    console.print("\n[bold]Fetching account balance…[/]")
    try:
        info = client.get_account_info()
    except Exception as e:
        console.print(f"[bold red]Failed to fetch account:[/] {e}\n")
        return

    assets = [a for a in info.get("assets", []) if float(a.get("walletBalance", 0)) > 0]
    if not assets:
        console.print("[dim]No balances found.[/]\n")
        return

    table = Table(title="Account Balances", box=box.ROUNDED, title_style="bold blue")
    table.add_column("Asset",          style="bold cyan")
    table.add_column("Wallet Balance", justify="right")
    table.add_column("Unrealized PnL", justify="right")
    table.add_column("Margin Balance", justify="right")

    for a in assets:
        pnl = float(a.get("unrealizedProfit", 0))
        pnl_style = "green" if pnl >= 0 else "red"
        table.add_row(
            a["asset"],
            a.get("walletBalance", "—"),
            Text(f"{pnl:+.4f}", style=pnl_style),
            a.get("marginBalance", "—"),
        )

    console.print()
    console.print(table)
    console.print()


# ── Interactive menu ──────────────────────────────────────────────────────────

def interactive_mode(client: BinanceClient):
    while True:
        console.print()
        action = questionary.select(
            "What would you like to do?",
            choices=[
                "📈  Place an order",
                "💰  View account balance",
                "🚪  Exit",
            ],
            style=Q_STYLE,
        ).ask()

        if action is None or "Exit" in action:
            console.print("\n[dim]Goodbye.[/]\n")
            break
        elif "balance" in action:
            show_balance(client)
        elif "order" in action:
            _interactive_order(client)


def _interactive_order(client: BinanceClient):
    console.print()

    # ── Symbol ────────────────────────────────────────────────────────────────
    symbol = questionary.select(
        "Select trading pair:",
        choices=VALID_SYMBOLS,
        style=Q_STYLE,
    ).ask()
    if symbol is None:
        return

    price_now = fetch_price(client, symbol)
    console.print(f"  [dim]Current {symbol} price:[/] [bold cyan]{price_now}[/]")

    # ── Side ──────────────────────────────────────────────────────────────────
    side = questionary.select(
        "Order side:",
        choices=["BUY", "SELL"],
        style=Q_STYLE,
    ).ask()
    if side is None:
        return

    # ── Order type ────────────────────────────────────────────────────────────
    order_type_display = questionary.select(
        "Order type:",
        choices=list(ORDER_TYPE_DESCRIPTIONS.values()),
        style=Q_STYLE,
    ).ask()
    if order_type_display is None:
        return
    # Extract the key (first word before spaces)
    order_type = order_type_display.split()[0]

    # ── Quantity ──────────────────────────────────────────────────────────────
    quantity = questionary.text(
        "Quantity:",
        validate=lambda v: True if _is_positive_float(v) else "Enter a positive number",
        style=Q_STYLE,
    ).ask()
    if quantity is None:
        return

    # ── Limit price ───────────────────────────────────────────────────────────
    price = None
    if order_type in LIMIT_ORDER_TYPES:
        price = questionary.text(
            f"Limit price (current: {price_now}):",
            validate=lambda v: True if _is_positive_float(v) else "Enter a positive number",
            style=Q_STYLE,
        ).ask()
        if price is None:
            return

    # ── Stop price ────────────────────────────────────────────────────────────
    stop_price = None
    if order_type in STOP_ORDER_TYPES:
        label = "Stop price (trigger):"
        stop_price = questionary.text(
            label,
            validate=lambda v: True if _is_positive_float(v) else "Enter a positive number",
            style=Q_STYLE,
        ).ask()
        if stop_price is None:
            return

    # ── Confirm ───────────────────────────────────────────────────────────────
    console.print()
    _print_order_preview(symbol, side, order_type, quantity, price, stop_price)
    confirm = questionary.confirm("Place this order?", default=True, style=Q_STYLE).ask()
    if not confirm:
        console.print("[dim]Order cancelled.[/]\n")
        return

    place_order(client, symbol, side, order_type, quantity, price, stop_price)


def _print_order_preview(symbol, side, order_type, quantity, price, stop_price):
    """Show a preview panel before confirming."""
    lines = [
        f"[dim]Symbol    :[/] [bold cyan]{symbol}[/]",
        f"[dim]Side      :[/] [bold]{'[green]' if side=='BUY' else '[red]'}{side}[/]",
        f"[dim]Type      :[/] [bold]{order_type}[/]",
        f"[dim]Quantity  :[/] [bold]{quantity}[/]",
    ]
    if price:
        lines.append(f"[dim]Limit Price:[/] [bold]{price}[/]")
    if stop_price:
        lines.append(f"[dim]Stop Price:[/]  [bold]{stop_price}[/]")

    console.print(Panel(
        "\n".join(lines),
        title="[bold]Order Preview[/]",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(0, 2),
    ))


def _is_positive_float(s: str) -> bool:
    try:
        return float(s) > 0
    except ValueError:
        return False


# ── CLI (non-interactive) mode ────────────────────────────────────────────────

def cli_mode(args: argparse.Namespace, client: BinanceClient):
    place_order(
        client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.type,
        quantity=str(args.quantity),
        price=str(args.price) if args.price else None,
        stop_price=str(args.stop_price) if args.stop_price else None,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py                                                        # interactive
  python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3500
  python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 60000
  python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.001 --price 62000 --stop-price 61000
        """
    )
    parser.add_argument("--symbol",     help=f"Trading pair ({', '.join(VALID_SYMBOLS)})")
    parser.add_argument("--side",       help=f"BUY or SELL")
    parser.add_argument("--type",       help=f"Order type ({', '.join(VALID_ORDER_TYPES)})")
    parser.add_argument("--quantity",   type=float, help="Order quantity")
    parser.add_argument("--price",      type=float, help="Limit price (LIMIT / STOP_LIMIT / TAKE_PROFIT)")
    parser.add_argument("--stop-price", type=float, dest="stop_price",
                        help="Stop/trigger price (STOP_* / TAKE_PROFIT_* types)")
    return parser


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    console.print(BANNER)
    logger.info("Trading bot CLI started.")

    api_key, api_secret = get_credentials()
    client = BinanceClient(api_key, api_secret)

    parser = build_parser()
    args = parser.parse_args()

    required_cli = [args.symbol, args.side, args.type, args.quantity]
    if all(a is not None for a in required_cli):
        cli_mode(args, client)
    elif any(a is not None for a in required_cli):
        console.print("[bold red][!][/] Provide all of: --symbol --side --type --quantity\n")
        parser.print_help()
        sys.exit(1)
    else:
        interactive_mode(client)

    logger.info("Trading bot CLI finished.")


if __name__ == "__main__":
    main()
