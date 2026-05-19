import logging
import requests
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("eToroIntegration")

logger.info('Starting Script')

# 1. API Configuration Configuration
BASE_URL = "https://public-api.etoro.com/api/v1"
API_KEY = "your_public_api_key_here"
USER_KEY = "your_user_key_here"

# Set up global headers required for all eToro endpoints
headers = {
    "x-api-key": API_KEY,
    "x-user-key": USER_KEY,
    "Content-Type": "application/json"
}

def get_instrument_id(ticker: str) -> int:
    """Resolves a ticker string into eToro's internal numeric InstrumentId"""
    url = f"{BASE_URL}/market-data/search"

    # Every separate request to eToro requires a unique tracking UUID
    request_headers = headers.copy()
    request_headers["x-request-id"] = str(uuid.uuid4())

    params = {"internalSymbolFull": ticker}

    response = requests.get(url, headers=request_headers, params=params)
    response.raise_for_status()

    data = response.json()
    # Extract the numeric ID from the response schema
    return data.get("InstrumentID")

def open_position_by_amount(instrument_id: int, usd_amount: float):
    """Executes a market buy order using a fixed cash dollar amount"""
    # Use the demo endpoint if testing to ensure you aren't deploying live capital!
    url = f"{BASE_URL}/trading/execution/demo/market-open-orders/by-amount"

    request_headers = headers.copy()
    request_headers["x-request-id"] = str(uuid.uuid4())

    payload = {
        "InstrumentId": instrument_id,
        "Amount": usd_amount,
        "Leverage": 1,         # 1x for standard underlying asset
        "StopLoss": None,      # Optional configuration parameters
        "TakeProfit": None
    }

    response = requests.post(url, headers=request_headers, json=payload)
    response.raise_for_status()
    return response.json()

# --- Execution Example ---
if __name__ == "__main__":
    try:
        # Step 1: Find out what ID eToro uses for Bitcoin
        target_ticker = "BTC"
        inst_id = get_instrument_id(target_ticker)
        print(f"Found Instrument ID for {target_ticker}: {inst_id}")

        # Step 2: Buy $1,000 worth of it in the demo environment
        order_status = open_position_by_amount(inst_id, 1000.00)
        print("Order Executed Successfully:")
        print(order_status)

    except Exception as e:
        print(f"API Integration Error: {e}")
