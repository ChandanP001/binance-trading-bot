"""
validators.py — Input validation layer
All user inputs are checked here before any API call is made.
"""

VALID_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"]
VALID_SIDES = ["BUY", "SELL"]
VALID_ORDER_TYPES = ["MARKET", "LIMIT", "STOP_MARKET"]


class ValidationError(Exception):
    """Raised when user input fails validation."""
    pass


def validate_symbol(symbol: str) -> str:
    if not symbol:
        raise ValidationError("Symbol cannot be empty.")
    symbol = symbol.strip().upper()
    if len(symbol) < 5:
        raise ValidationError(f"Symbol '{symbol}' is too short. Example: BTCUSDT")
    return symbol


def validate_side(side: str) -> str:
    if not side:
        raise ValidationError("Side cannot be empty.")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}")
    return side


def validate_order_type(order_type: str) -> str:
    if not order_type:
        raise ValidationError("Order type cannot be empty.")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(VALID_ORDER_TYPES)}"
        )
    return order_type


def validate_quantity(quantity) -> float:
    if quantity is None:
        raise ValidationError("Quantity cannot be empty.")
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        raise ValidationError(f"Quantity must be a number. Got: '{quantity}'")
    if qty <= 0:
        raise ValidationError(f"Quantity must be positive. Got: {qty}")
    if qty > 1000:
        raise ValidationError(f"Quantity {qty} seems too large. Max allowed: 1000")
    return qty


def validate_price(price, order_type: str):
    if order_type in ("MARKET", "STOP_MARKET"):
        return None  # these order types don't use a limit price
    if price is None:
        raise ValidationError(f"Price is required for {order_type} orders.")
    try:
        p = float(price)
    except (ValueError, TypeError):
        raise ValidationError(f"Price must be a number. Got: '{price}'")
    if p <= 0:
        raise ValidationError(f"Price must be positive. Got: {p}")
    return p


def validate_stop_price(stop_price, order_type: str):
    if order_type != "STOP_MARKET":
        return None
    if stop_price is None:
        raise ValidationError("Stop price is required for STOP_MARKET orders.")
    try:
        sp = float(stop_price)
    except (ValueError, TypeError):
        raise ValidationError(f"Stop price must be a number. Got: '{stop_price}'")
    if sp <= 0:
        raise ValidationError(f"Stop price must be positive. Got: {sp}")
    return sp


def validate_all(symbol, side, order_type, quantity, price=None, stop_price=None):
    """Run all validators and return cleaned values."""
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity = validate_quantity(quantity)
    price = validate_price(price, order_type)
    stop_price = validate_stop_price(stop_price, order_type)
    return symbol, side, order_type, quantity, price, stop_price
