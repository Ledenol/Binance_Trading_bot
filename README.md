# Binance Futures Testnet — Trading Bot

A Python CLI application for placing orders on the [Binance Futures Testnet](https://testnet.binancefuture.com). Clean architecture, rich terminal UI, and all bonus features implemented.

---

## Features

**Core**
- Place MARKET and LIMIT orders on USDT-M Futures Testnet
- Input validation with clear error messages
- Structured logging to console + rotating file

**Bonus (all three implemented)**
- ✅ Extra order types: STOP_MARKET, STOP_LIMIT, TAKE_PROFIT_MARKET, TAKE_PROFIT
- ✅ Enhanced CLI UX with arrow-key menus (questionary), live price display, order preview panel, and colour output (rich)
- ✅ Account balance viewer built into the menu

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST API wrapper
│   ├── orders.py          # Order logic + rich-formatted output
│   ├── validators.py      # Input validation for all order types
│   ├── logging_config.py  # Console + rotating file logging
│   └── cli.py             # CLI entry point (interactive + args)
├── logs/
│   └── trading_bot.log    # Sample log with MARKET + LIMIT orders
├── README.md
└── requirements.txt
```

---

## Setup

### 1. Get Testnet API Credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your **Google** (no KYC, no real money)
3. Click **API Key** at the top → credentials are auto-generated
4. Copy your **API Key** and **Secret Key**

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables

```bash
export BINANCE_TESTNET_API_KEY="your_api_key_here"
export BINANCE_TESTNET_API_SECRET="your_api_secret_here"
```

---

## How to Run

### Interactive Mode (recommended)

```bash
cd bot
python cli.py
```

You'll see a full arrow-key menu:

```
? What would you like to do?
 ❯ 📈  Place an order
   💰  View account balance
   🚪  Exit
```

Selecting **Place an order** walks you through:
1. Symbol (arrow-key list)
2. Live current price is displayed
3. Side (BUY / SELL)
4. Order type (with descriptions)
5. Quantity, limit price, stop price (only shown when relevant)
6. Order preview panel → confirm before sending

### CLI / Script Mode

```bash
cd bot

# MARKET buy
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# LIMIT sell
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3500

# Stop-market (closes position if price drops to 60000)
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 60000

# Stop-limit
python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.001 --price 62000 --stop-price 61000

# Take-profit market
python cli.py --symbol BTCUSDT --side SELL --type TAKE_PROFIT_MARKET --quantity 0.001 --stop-price 75000
```

### Help

```bash
python cli.py --help
```

---

## Order Types Supported

| Type | Needs Limit Price | Needs Stop Price | Description |
|---|---|---|---|
| MARKET | ✗ | ✗ | Instant fill at market |
| LIMIT | ✓ | ✗ | Fill at price or better |
| STOP_MARKET | ✗ | ✓ | Market order triggered at stop price |
| STOP_LIMIT | ✓ | ✓ | Limit order triggered at stop price |
| TAKE_PROFIT_MARKET | ✗ | ✓ | Market close at profit target |
| TAKE_PROFIT | ✓ | ✓ | Limit close at profit target |

---

## Logging

All API requests, responses, and errors are written to `logs/trading_bot.log`.

- **Console**: INFO and above  
- **File**: DEBUG and above (rotating, max 5 MB × 3 backups)

---

## Assumptions

- Uses direct REST calls (`requests`) — no Binance SDK dependency
- Supported symbols: `BTCUSDT`, `ETHUSDT`, `BNBUSDT`, `XRPUSDT`, `SOLUSDT` — extend `VALID_SYMBOLS` in `validators.py` to add more
- LIMIT-type orders use `timeInForce=GTC` by default
- Credentials loaded from environment variables only — never hardcoded
---

## Bonus Features

All three optional bonus features from the task have been implemented.

### 1. Extra Order Types

In addition to MARKET and LIMIT, the bot supports:

| Type | Description |
|---|---|
| STOP_MARKET | Triggers a market order when price hits the stop level |
| STOP_LIMIT | Triggers a limit order when price hits the stop level |
| TAKE_PROFIT_MARKET | Closes position at a profit target using a market order |
| TAKE_PROFIT | Closes position at a profit target using a limit order |

Implemented across `validators.py` (type rules and stop price validation), `client.py` (stopPrice parameter passed to API), and `cli.py` (stop price prompt appears only when the selected order type requires it).

### 2. Enhanced CLI UX

- Arrow-key dropdown menus via `questionary` — no typing required for symbol, side, or order type
- Live price fetched from the API and displayed the moment you select a symbol
- Order types shown with plain-English descriptions, not just raw type names
- Order preview panel shown before confirming — shows all parameters before anything is sent
- Full colour terminal output via `rich` — results, errors, and status all colour coded

### 3. Account Balance Viewer

Accessible from the main menu under **View account balance**. Fetches your testnet account from the API and displays a formatted table showing wallet balance, margin balance, and unrealised PnL per asset, with PnL colour coded green or red.
