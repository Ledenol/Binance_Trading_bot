"""
validators.py - Input validation for trading bot CLI and order parameters.
"""

VALID_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"]
VALID_SIDES = ["BUY", "SELL"]
VALID_ORDER_TYPES = ["MARKET", "LIMIT", "STOP_MARKET", "STOP_LIMIT", "TAKE_PROFIT_MARKET", "TAKE_PROFIT"]

# Types that require a stop price
STOP_ORDER_TYPES = ["STOP_MARKET", "STOP_LIMIT", "TAKE_PROFIT_MARKET", "TAKE_PROFIT"]
# Types that require a limit price
LIMIT_ORDER_TYPES = ["LIMIT", "STOP_LIMIT", "TAKE_PROFIT"]


class ValidationError(Exception):
    """Raised when user input fails validation."""
    pass


def validate_symbol(symbol: str) -> str:
    """Validate and normalize the trading symbol."""
    symbol = symbol.strip().upper()
    if symbol not in VALID_SYMBOLS:
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Valid symbols: {', '.join(VALID_SYMBOLS)}"
        )
    return symbol


def validate_side(side: str) -> str:
    """Validate and normalize the order side."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}"
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Validate and normalize the order type."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(VALID_ORDER_TYPES)}"
        )
    return order_type


def validate_quantity(quantity_str: str) -> float:
    """Validate and parse the order quantity."""
    try:
        qty = float(quantity_str)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid quantity '{quantity_str}'. Must be a positive number.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than 0, got {qty}.")
    return qty


def validate_price(price_str: str) -> float:
    """Validate and parse the order price (for LIMIT orders)."""
    try:
        price = float(price_str)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid price '{price_str}'. Must be a positive number.")
    if price <= 0:
        raise ValidationError(f"Price must be greater than 0, got {price}.")
    return price


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str = None,
    stop_price: str = None,
) -> dict:
    """
    Validate all order parameters at once.

    Returns:
        dict with validated and typed values
    Raises:
        ValidationError if any parameter is invalid
    """
    validated = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": None,
        "stop_price": None,
    }

    ot = validated["order_type"]

    # Limit price required for LIMIT and STOP_LIMIT and TAKE_PROFIT
    if ot in LIMIT_ORDER_TYPES:
        if price is None or str(price).strip() == "":
            raise ValidationError(f"Limit price is required for {ot} orders.")
        validated["price"] = validate_price(str(price))

    # Stop price required for all stop/take-profit types
    if ot in STOP_ORDER_TYPES:
        if stop_price is None or str(stop_price).strip() == "":
            raise ValidationError(f"Stop price is required for {ot} orders.")
        validated["stop_price"] = validate_price(str(stop_price))

    return validated
