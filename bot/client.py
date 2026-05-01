"""
client.py - Binance Futures Testnet API client wrapper
Handles all direct REST API interactions with the Binance Futures Testnet.
"""

import time
import hashlib
import hmac
import requests
from urllib.parse import urlencode
from logging_config import get_logger

logger = get_logger(__name__)

BASE_URL = "https://testnet.binancefuture.com"


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        })

    def _sign(self, params: dict) -> dict:
        """Add HMAC SHA256 signature to params."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        params["signature"] = signature
        return params

    def _get(self, endpoint: str, params: dict = None, signed: bool = False) -> dict:
        """Send a GET request."""
        params = params or {}
        if signed:
            params = self._sign(params)
        url = f"{BASE_URL}{endpoint}"
        logger.info(f"GET {url} | params={params}")
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response: {data}")
            return data
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error on GET {url}: {e} | Body: {response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error on GET {url}: {e}")
            raise

    def _post(self, endpoint: str, params: dict = None) -> dict:
        """Send a signed POST request."""
        params = params or {}
        params = self._sign(params)
        url = f"{BASE_URL}{endpoint}"
        logger.info(f"POST {url} | params={params}")
        try:
            response = self.session.post(url, data=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response: {data}")
            return data
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error on POST {url}: {e} | Body: {response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error on POST {url}: {e}")
            raise

    def get_account_info(self) -> dict:
        """Fetch account/balance information."""
        return self._get("/fapi/v2/account", signed=True)

    def get_exchange_info(self) -> dict:
        """Fetch exchange trading rules and symbol info."""
        return self._get("/fapi/v1/exchangeInfo")

    def get_symbol_price(self, symbol: str) -> dict:
        """Fetch the latest price for a symbol."""
        return self._get("/fapi/v1/ticker/price", params={"symbol": symbol})

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
        stop_price: float = None,
        time_in_force: str = "GTC"
    ) -> dict:
        """
        Place a MARKET, LIMIT, STOP_MARKET, STOP_LIMIT, TAKE_PROFIT_MARKET,
        or TAKE_PROFIT order.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: BUY or SELL
            order_type: One of the supported types
            quantity: Order quantity
            price: Required for LIMIT / STOP_LIMIT / TAKE_PROFIT
            stop_price: Required for STOP_* and TAKE_PROFIT_* types
            time_in_force: GTC, IOC, FOK (only for LIMIT-type orders)
        """
        from validators import LIMIT_ORDER_TYPES, STOP_ORDER_TYPES
        ot = order_type.upper()
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": ot,
            "quantity": quantity,
        }
        if ot in LIMIT_ORDER_TYPES:
            if price is None:
                raise ValueError(f"Price is required for {ot} orders.")
            params["price"] = price
            params["timeInForce"] = time_in_force
        if ot in STOP_ORDER_TYPES:
            if stop_price is None:
                raise ValueError(f"Stop price is required for {ot} orders.")
            params["stopPrice"] = stop_price

        return self._post("/fapi/v1/order", params=params)

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Query a specific order by ID."""
        return self._get("/fapi/v1/order", params={"symbol": symbol, "orderId": order_id}, signed=True)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open order."""
        params = self._sign({"symbol": symbol, "orderId": order_id})
        url = f"{BASE_URL}/fapi/v1/order"
        logger.info(f"DELETE {url} | params={params}")
        try:
            response = self.session.delete(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response: {data}")
            return data
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error cancelling order: {e} | Body: {response.text}")
            raise
