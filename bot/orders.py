"""
orders.py — Order placement logic and output formatting
Sits between the CLI and the API client.
"""

from bot.client import BinanceFuturesClient, BinanceClientError, NetworkError
from bot.logging_config import get_logger

logger = get_logger("orders")

DIVIDER = "=" * 57


def format_order_summary(symbol, side, order_type, quantity, price=None, stop_price=None) -> str:
    lines = [
        DIVIDER,
        "           ORDER REQUEST SUMMARY",
        DIVIDER,
        f"  Symbol     : {symbol}",
        f"  Side       : {side}",
        f"  Type       : {order_type}",
        f"  Quantity   : {quantity}",
    ]
    if price is not None:
        lines.append(f"  Price      : {price}")
    if stop_price is not None:
        lines.append(f"  Stop Price : {stop_price}")
    lines.append(DIVIDER)
    return "\n".join(lines)


def format_order_response(response: dict) -> str:
    mock_label = "  ⚠️  [MOCK MODE — simulated response]\n" if response.get("_mock") else ""
    lines = [
        DIVIDER,
        "           ORDER RESPONSE",
        DIVIDER,
        mock_label,
        f"  Order ID      : {response.get('orderId', 'N/A')}",
        f"  Client OID    : {response.get('clientOrderId', 'N/A')}",
        f"  Symbol        : {response.get('symbol', 'N/A')}",
        f"  Side          : {response.get('side', 'N/A')}",
        f"  Type          : {response.get('type', 'N/A')}",
        f"  Status        : {response.get('status', 'N/A')}",
        f"  Orig Qty      : {response.get('origQty', 'N/A')}",
        f"  Executed Qty  : {response.get('executedQty', 'N/A')}",
        f"  Avg Price     : {response.get('avgPrice', 'N/A')}",
        DIVIDER,
    ]
    return "\n".join(lines)


def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float = None,
    stop_price: float = None,
) -> dict:
    print(format_order_summary(symbol, side, order_type, quantity, price, stop_price))

    try:
        response = client.place_order(symbol, side, order_type, quantity, price, stop_price)
        print(format_order_response(response))
        print(f"  ✅  ORDER {'SIMULATED' if response.get('_mock') else 'PLACED'} SUCCESSFULLY\n")
        logger.info(
            f"ORDER SUCCESS | orderId={response.get('orderId')} | status={response.get('status')}"
        )
        return response

    except BinanceClientError as e:
        print(f"\n  ❌  BINANCE API ERROR: {e}\n")
        logger.error(f"ORDER FAILED — BinanceClientError: {e}")
        return {}

    except NetworkError as e:
        print(f"\n  ❌  NETWORK ERROR: {e}\n")
        logger.error(f"ORDER FAILED — NetworkError: {e}")
        return {}

    except Exception as e:
        print(f"\n  ❌  UNEXPECTED ERROR: {e}\n")
        logger.error(f"ORDER FAILED — Unexpected: {e}")
        return {}


def get_account_info(client: BinanceFuturesClient) -> dict:
    try:
        data = client.get_account()
        mock_label = "  ⚠️  [MOCK MODE — simulated balance]\n" if data.get("_mock") else ""
        print(DIVIDER)
        print("           ACCOUNT INFO")
        print(DIVIDER)
        if mock_label:
            print(mock_label)
        print(f"  Wallet Balance   : {data.get('totalWalletBalance', 'N/A')} USDT")
        print(f"  Margin Balance   : {data.get('totalMarginBalance', 'N/A')} USDT")
        print(f"  Available        : {data.get('availableBalance', 'N/A')} USDT")
        print(f"  Unrealised PnL   : {data.get('totalUnrealizedProfit', 'N/A')} USDT")
        print(DIVIDER)
        return data
    except (BinanceClientError, NetworkError) as e:
        print(f"\n  ❌  ERROR fetching account: {e}\n")
        logger.error(f"ACCOUNT FETCH FAILED: {e}")
        return {}


def get_open_orders(client: BinanceFuturesClient, symbol: str = None) -> list:
    try:
        orders = client.get_open_orders(symbol)
        print(DIVIDER)
        print("           OPEN ORDERS")
        print(DIVIDER)
        if not orders:
            print("  No open orders found.")
        for o in orders:
            print(
                f"  [{o.get('orderId')}] {o.get('symbol')} | "
                f"{o.get('side')} {o.get('origQty')} @ {o.get('price')} | {o.get('status')}"
            )
        print(DIVIDER)
        return orders
    except (BinanceClientError, NetworkError) as e:
        print(f"\n  ❌  ERROR fetching orders: {e}\n")
        logger.error(f"OPEN ORDERS FETCH FAILED: {e}")
        return []
