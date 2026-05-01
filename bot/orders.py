"""
orders.py - Order placement logic and rich-formatted response display.
"""

from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text

from client import BinanceClient
from validators import validate_order_params, ValidationError
from logging_config import get_logger

logger = get_logger(__name__)
console = Console()

STATUS_STYLE = {
    "FILLED": "bold green",
    "NEW": "bold yellow",
    "PARTIALLY_FILLED": "bold cyan",
    "CANCELED": "bold red",
    "REJECTED": "bold red",
}


def _print_order_summary(order: dict):
    """Print a rich-formatted order summary table."""
    status = order.get("status", "UNKNOWN")
    style = STATUS_STYLE.get(status, "white")

    table = Table(
        title="Order Summary",
        box=box.ROUNDED,
        title_style="bold blue",
        show_header=False,
        min_width=44,
    )
    table.add_column("Field", style="dim", width=16)
    table.add_column("Value", style="bold")

    avg_price = order.get("avgPrice") or order.get("price") or "0"
    if float(avg_price) == 0:
        avg_price = "—"

    rows = [
        ("Order ID", str(order.get("orderId", "—"))),
        ("Symbol", order.get("symbol", "—")),
        ("Side", order.get("side", "—")),
        ("Type", order.get("type", "—")),
        ("Status", Text(status, style=style)),
        ("Qty Ordered", str(order.get("origQty", "—"))),
        ("Qty Filled", str(order.get("executedQty", "—"))),
        ("Avg Price", str(avg_price)),
    ]

    stop = order.get("stopPrice")
    if stop and float(stop) > 0:
        rows.append(("Stop Price", str(stop)))

    for field, value in rows:
        table.add_row(field, value)

    console.print()
    console.print(table)

    if status in ("FILLED", "NEW", "PARTIALLY_FILLED"):
        console.print(f"  [bold green]✓[/] Order placed successfully — Status: [bold]{status}[/]\n")
    else:
        console.print(f"  [bold red]✗[/] Unexpected status: [bold]{status}[/]\n")


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str = None,
    stop_price: str = None,
) -> bool:
    """
    Validate inputs, place an order, and print a rich summary.
    Returns True if successful, False otherwise.
    """
    try:
        params = validate_order_params(symbol, side, order_type, quantity, price, stop_price)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        console.print(f"\n  [bold red][!] Validation Error:[/] {e}\n")
        return False

    logger.info(
        f"Placing {params['order_type']} {params['side']} order | "
        f"Symbol={params['symbol']} Qty={params['quantity']} "
        f"Price={params.get('price')} StopPrice={params.get('stop_price')}"
    )

    try:
        order = client.place_order(
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params.get("price"),
            stop_price=params.get("stop_price"),
        )
    except Exception as e:
        logger.error(f"Order placement failed: {e}")
        console.print(f"\n  [bold red][!] Order Failed:[/] {e}\n")
        return False

    _print_order_summary(order)
    return order.get("status") in ("FILLED", "NEW", "PARTIALLY_FILLED")
