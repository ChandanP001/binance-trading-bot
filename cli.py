"""
cli.py — Command-line interface entry point
Usage examples:
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --qty 0.001 --price 90000
  python cli.py place --symbol BTCUSDT --side BUY --type STOP_MARKET --qty 0.001 --stop-price 80000
  python cli.py account
  python cli.py orders
  python cli.py orders --symbol BTCUSDT

Add --mock to any command to run in simulation mode (no API key needed):
  python cli.py --mock place --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
  python cli.py --mock account
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logger, get_logger
from bot.orders import place_order, get_account_info, get_open_orders
from bot.validators import validate_all, ValidationError

# Initialise logging immediately
setup_logger()
logger = get_logger("cli")


BANNER = """
╔══════════════════════════════════════════════════╗
║      Binance Futures Testnet Trading Bot         ║
║      Primetrade.ai Assignment                    ║
╚══════════════════════════════════════════════════╝
"""


def get_client(mock_mode: bool = False) -> BinanceFuturesClient:
    """Load credentials from .env and return a configured client."""
    load_dotenv()
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")

    if not mock_mode and (not api_key or not api_secret):
        print("\n  ⚠️  No API credentials found in .env — switching to MOCK mode automatically.\n")
        mock_mode = True

    return BinanceFuturesClient(api_key=api_key, api_secret=api_secret, mock_mode=mock_mode)


# ------------------------------------------------------------------ #
#  Command handlers                                                    #
# ------------------------------------------------------------------ #

def cmd_place(args):
    logger.info(
        f"CLI COMMAND: place | symbol={args.symbol} side={args.side} "
        f"type={args.type} qty={args.qty} price={args.price} stop={args.stop_price}"
    )

    try:
        symbol, side, order_type, quantity, price, stop_price = validate_all(
            args.symbol, args.side, args.type, args.qty, args.price, args.stop_price
        )
    except ValidationError as e:
        print(f"\n  ❌  VALIDATION ERROR: {e}\n")
        logger.warning(f"VALIDATION FAILED: {e}")
        sys.exit(1)

    client = get_client(mock_mode=args.mock)
    place_order(client, symbol, side, order_type, quantity, price, stop_price)


def cmd_account(args):
    logger.info("CLI COMMAND: account")
    client = get_client(mock_mode=args.mock)
    get_account_info(client)


def cmd_orders(args):
    logger.info(f"CLI COMMAND: orders | symbol={getattr(args, 'symbol', None)}")
    client = get_client(mock_mode=args.mock)
    get_open_orders(client, symbol=getattr(args, "symbol", None))


def cmd_cancel(args):
    logger.info(f"CLI COMMAND: cancel | symbol={args.symbol} orderId={args.order_id}")
    client = get_client(mock_mode=args.mock)
    try:
        result = client.cancel_order(args.symbol.upper(), int(args.order_id))
        print(f"\n  ✅  Order {result.get('orderId')} cancelled. Status: {result.get('status')}\n")
    except Exception as e:
        print(f"\n  ❌  Cancel failed: {e}\n")
        logger.error(f"CANCEL FAILED: {e}")


# ------------------------------------------------------------------ #
#  Argument parser                                                     #
# ------------------------------------------------------------------ #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot — Primetrade.ai Assignment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --mock place --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
  python cli.py --mock place --symbol ETHUSDT --side SELL --type LIMIT --qty 0.01 --price 1700
  python cli.py --mock place --symbol BTCUSDT --side BUY --type STOP_MARKET --qty 0.001 --stop-price 80000
  python cli.py --mock account
  python cli.py --mock orders
        """,
    )

    # Global flag — works before any subcommand
    parser.add_argument(
        "--mock",
        action="store_true",
        default=False,
        help="Run in mock/simulation mode — no real API calls, no credentials needed",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- place ---
    place_parser = subparsers.add_parser("place", help="Place a new order")
    place_parser.add_argument("--symbol", required=True, help="Trading pair (e.g. BTCUSDT)")
    place_parser.add_argument("--side", required=True, help="BUY or SELL")
    place_parser.add_argument("--type", required=True, help="MARKET, LIMIT, or STOP_MARKET")
    place_parser.add_argument("--qty", required=True, help="Order quantity")
    place_parser.add_argument("--price", default=None, help="Limit price (required for LIMIT)")
    place_parser.add_argument("--stop-price", dest="stop_price", default=None,
                               help="Stop price (required for STOP_MARKET)")
    place_parser.set_defaults(func=cmd_place)

    # --- account ---
    account_parser = subparsers.add_parser("account", help="Show account balance")
    account_parser.set_defaults(func=cmd_account)

    # --- orders ---
    orders_parser = subparsers.add_parser("orders", help="List open orders")
    orders_parser.add_argument("--symbol", default=None, help="Filter by symbol (optional)")
    orders_parser.set_defaults(func=cmd_orders)

    # --- cancel ---
    cancel_parser = subparsers.add_parser("cancel", help="Cancel an open order")
    cancel_parser.add_argument("--symbol", required=True, help="Trading pair")
    cancel_parser.add_argument("--order-id", dest="order_id", required=True, help="Order ID to cancel")
    cancel_parser.set_defaults(func=cmd_cancel)

    return parser


def main():
    print(BANNER)
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
