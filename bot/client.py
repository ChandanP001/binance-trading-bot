"""
client.py — Binance Futures API wrapper
Supports two modes:
  - LIVE mode: real HTTP calls to testnet.binancefuture.com
  - MOCK mode: simulated responses (for demo / when testnet is inaccessible)
"""

import hashlib
import hmac
import random
import string
import time
from urllib.parse import urlencode

import requests

from bot.logging_config import get_logger

logger = get_logger("client")

TESTNET_BASE_URL = "https://testnet.binancefuture.com"

# Approximate mock prices for simulation
MOCK_PRICES = {
    "BTCUSDT": 84500.0,
    "ETHUSDT": 1620.0,
    "BNBUSDT": 590.0,
    "SOLUSDT": 135.0,
    "XRPUSDT": 2.15,
    "ADAUSDT": 0.68,
}


class BinanceClientError(Exception):
    """Raised for Binance API-level errors (e.g., invalid symbol, bad credentials)."""
    pass


class NetworkError(Exception):
    """Raised for network/connectivity failures."""
    pass


def _generate_order_id() -> int:
    return random.randint(10_000_000, 99_999_999)


def _mock_order_response(symbol, side, order_type, quantity, price=None, stop_price=None) -> dict:
    """
    Generate a realistic mock order response that mirrors the real Binance API format.
    Used when MOCK_MODE=true or when testnet is unreachable.
    """
    mock_price = MOCK_PRICES.get(symbol, 100.0)

    if order_type == "MARKET":
        avg_price = mock_price * random.uniform(0.9995, 1.0005)  # slight slippage
        exec_qty = quantity
        status = "FILLED"
        price_out = 0  # Binance returns 0 for market order price field
    elif order_type == "LIMIT":
        avg_price = price
        exec_qty = 0.0  # limit orders start unfilled
        status = "NEW"
        price_out = price
    elif order_type == "STOP_MARKET":
        avg_price = 0.0
        exec_qty = 0.0
        status = "NEW"
        price_out = 0
    else:
        avg_price = mock_price
        exec_qty = quantity
        status = "FILLED"
        price_out = mock_price

    order_id = _generate_order_id()
    client_order_id = "".join(random.choices(string.ascii_letters + string.digits, k=16))

    return {
        "orderId": order_id,
        "symbol": symbol,
        "status": status,
        "clientOrderId": client_order_id,
        "price": str(price_out),
        "avgPrice": f"{avg_price:.2f}",
        "origQty": str(quantity),
        "executedQty": str(exec_qty),
        "cumQty": str(exec_qty),
        "cumQuote": str(round(exec_qty * avg_price, 4)),
        "timeInForce": "GTC" if order_type == "LIMIT" else "GTE_GTC",
        "type": order_type,
        "side": side,
        "stopPrice": str(stop_price or "0"),
        "workingType": "CONTRACT_PRICE",
        "priceProtect": False,
        "origType": order_type,
        "updateTime": int(time.time() * 1000),
        "_mock": True,
    }


def _mock_account_response() -> dict:
    return {
        "totalWalletBalance": "10000.00",
        "totalUnrealizedProfit": "0.00",
        "totalMarginBalance": "10000.00",
        "availableBalance": "10000.00",
        "assets": [
            {
                "asset": "USDT",
                "walletBalance": "10000.00",
                "availableBalance": "10000.00",
            }
        ],
        "_mock": True,
    }


def _mock_open_orders(symbol=None) -> list:
    return []


class BinanceFuturesClient:
    """
    Thin wrapper around the Binance Futures REST API.
    Set mock_mode=True to run without real API credentials.
    """

    def __init__(self, api_key: str = "", api_secret: str = "", mock_mode: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.mock_mode = mock_mode
        self.base_url = TESTNET_BASE_URL
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/json",
            }
        )
        mode_label = "MOCK" if mock_mode else "LIVE (testnet)"
        logger.info(f"BinanceFuturesClient initialised | mode={mode_label}")

    def _sign(self, params: dict) -> dict:
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(self, method: str, endpoint: str, params: dict = None, signed: bool = False):
        params = params or {}
        if signed:
            params = self._sign(params)

        url = f"{self.base_url}{endpoint}"
        logger.debug(f"REQUEST | {method} {endpoint} | params={params}")

        try:
            response = self.session.request(method, url, params=params, timeout=10)
            logger.debug(f"RESPONSE | status={response.status_code} | body={response.text[:500]}")
            data = response.json()
        except requests.exceptions.ConnectionError as e:
            logger.error(f"NETWORK ERROR | {e}")
            raise NetworkError(f"Cannot connect to Binance testnet: {e}")
        except requests.exceptions.Timeout:
            logger.error("NETWORK ERROR | Request timed out")
            raise NetworkError("Request timed out after 10 seconds.")
        except Exception as e:
            logger.error(f"UNEXPECTED ERROR | {e}")
            raise NetworkError(f"Unexpected error: {e}")

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            logger.error(f"BINANCE API ERROR | code={data['code']} | msg={data.get('msg')}")
            raise BinanceClientError(
                f"Binance API Error [{data['code']}]: {data.get('msg', 'Unknown error')}"
            )

        return data

    # ------------------------------------------------------------------ #
    #  Public methods                                                       #
    # ------------------------------------------------------------------ #

    def get_server_time(self) -> dict:
        if self.mock_mode:
            return {"serverTime": int(time.time() * 1000), "_mock": True}
        return self._request("GET", "/fapi/v1/time")

    def get_account(self) -> dict:
        if self.mock_mode:
            logger.info("MOCK | Returning simulated account balance")
            return _mock_account_response()
        return self._request("GET", "/fapi/v2/account", signed=True)

    def get_open_orders(self, symbol: str = None) -> list:
        if self.mock_mode:
            logger.info("MOCK | Returning empty open orders list")
            return _mock_open_orders(symbol)
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        if self.mock_mode:
            logger.info(f"MOCK | Simulating cancel for orderId={order_id}")
            return {"orderId": order_id, "symbol": symbol, "status": "CANCELED", "_mock": True}
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("DELETE", "/fapi/v1/order", params=params, signed=True)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
        stop_price: float = None,
    ) -> dict:
        logger.info(
            f"PLACING ORDER | symbol={symbol} | side={side} | type={order_type} "
            f"| qty={quantity} | price={price} | stopPrice={stop_price}"
        )

        if self.mock_mode:
            logger.info("MOCK | Generating simulated order response")
            time.sleep(0.3)  # simulate network latency
            response = _mock_order_response(symbol, side, order_type, quantity, price, stop_price)
            logger.info(f"MOCK ORDER PLACED | orderId={response['orderId']} | status={response['status']}")
            return response

        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = "GTC"
        elif order_type == "STOP_MARKET":
            params["stopPrice"] = stop_price

        return self._request("POST", "/fapi/v1/order", params=params, signed=True)
