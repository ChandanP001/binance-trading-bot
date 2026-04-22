# Binance Futures Testnet Trading Bot

A lightweight Python CLI application that places orders on the **Binance Futures Testnet (USDT-M)** with clean 4-layer architecture, structured logging, and full error handling.

Supports a **mock/simulation mode** — runs without any API credentials, producing realistic responses that mirror the real Binance API format. This is useful for testing, demos, and environments where the Binance testnet is inaccessible.

---

## Project Structure

```
binance-trading-bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance API wrapper (LIVE + MOCK modes)
│   ├── orders.py          # Order placement logic and output formatting
│   ├── validators.py      # Input validation layer
│   └── logging_config.py  # Structured logging (file + console)
├── logs/                  # Auto-created, contains daily log files
├── cli.py                 # CLI entry point (argparse)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/binance-trading-bot.git
cd binance-trading-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API credentials (for LIVE mode only)

```bash
cp .env.example .env
```

Edit `.env` and paste your Binance Futures Testnet credentials:

```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

Get testnet credentials at: https://testnet.binancefuture.com

> **Note:** If you don't have testnet credentials, use `--mock` mode — no credentials needed.

---

## How to Run

### Mock mode (no credentials needed — recommended for quick demo)

```bash
# Market BUY
python cli.py --mock place --symbol BTCUSDT --side BUY --type MARKET --qty 0.001

# Limit SELL
python cli.py --mock place --symbol BTCUSDT --side SELL --type LIMIT --qty 0.001 --price 90000

# Stop Market (bonus order type)
python cli.py --mock place --symbol BTCUSDT --side BUY --type STOP_MARKET --qty 0.001 --stop-price 80000

# Account balance
python cli.py --mock account

# Open orders
python cli.py --mock orders
python cli.py --mock orders --symbol BTCUSDT
```

### Live mode (with real testnet credentials in .env)

```bash
# Same commands — just remove --mock
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
python cli.py place --symbol ETHUSDT --side SELL --type LIMIT --qty 0.01 --price 1700
python cli.py account
```

> If no credentials are found in `.env`, the bot automatically switches to mock mode.

---

## Order Types Supported

| Type | Description | Required params |
|------|-------------|-----------------|
| `MARKET` | Executes immediately at current market price | `--qty` |
| `LIMIT` | Executes only at specified price or better | `--qty --price` |
| `STOP_MARKET` | Triggers a market order when stop price is hit | `--qty --stop-price` |

---

## Sample Output

```
╔══════════════════════════════════════════════════╗
║      Binance Futures Testnet Trading Bot         ║
║      Primetrade.ai Assignment                    ║
╚══════════════════════════════════════════════════╝

=========================================================
           ORDER REQUEST SUMMARY
=========================================================
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
=========================================================
  Order ID      : 37154947
  Status        : FILLED
  Executed Qty  : 0.001
  Avg Price     : 84469.62
=========================================================
  ✅  ORDER SIMULATED SUCCESSFULLY
```

---

## Logging

Logs are written to `logs/trading_bot_YYYYMMDD.log`.

- **File:** captures DEBUG level — full request/response bodies, all events
- **Console:** INFO level only — clean summary for the user

Log format:
```
2026-04-21 13:16:51 | INFO     | trading_bot.client | MOCK ORDER PLACED | orderId=99539953 | status=FILLED
```

---

## Assumptions & Design Decisions

1. **Mock mode** mirrors the real Binance Futures API response schema exactly — `orderId`, `status`, `executedQty`, `avgPrice` all follow the real format, making it straightforward to swap in live credentials.

2. **MARKET orders** return `status=FILLED` with simulated slippage (±0.05%). **LIMIT orders** return `status=NEW` since they are resting orders waiting to fill.

3. **STOP_MARKET** is implemented as the bonus third order type. It triggers a market order when price hits the stop level — the primary use case is stop-loss protection.

4. **Validation runs before any API call.** Invalid inputs (wrong symbol format, negative quantity, missing price for LIMIT) are caught and reported with clear messages without touching the network.

5. **timeInForce=GTC** (Good Till Cancelled) is used for LIMIT orders — the order stays open until filled or manually cancelled.

6. **Credentials auto-fallback:** If `BINANCE_API_KEY` is missing or empty, the bot switches to mock mode automatically rather than crashing.

---

## Error Handling

Three distinct exception types:

- `ValidationError` — bad user input, caught before any API call
- `BinanceClientError` — API-level errors (invalid symbol, bad credentials, insufficient balance)
- `NetworkError` — connection failures, timeouts

Each produces a specific, actionable error message.

---

## Requirements

- Python 3.8+
- `requests` — HTTP calls to Binance REST API
- `python-dotenv` — load credentials from `.env`
