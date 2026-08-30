import atexit
import json
import logging
import os

from dotenv import load_dotenv
from trading_ig import IGService, IGStreamService

logger = logging.getLogger(__name__)

IG_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Api: https://labs.ig.com/rest-trading-api-reference.html
class IGTradingClient:
    def __init__(self, account_type: str):
        load_dotenv()
        self.acc_number = os.getenv(account_type + "_IG_SERVICE_ACC_NUMBER")
        self.ig_service = IGService(
            os.getenv(account_type + "_IG_SERVICE_USERNAME"),
            os.getenv(account_type + "_IG_SERVICE_PASSWORD"),
            os.getenv(account_type + "_IG_SERVICE_API_KEY"),
            os.getenv(account_type + "_IG_SERVICE_ACC_TYPE"),
            os.getenv(account_type + "_IG_SERVICE_ACC_NUMBER")
        )
        self.ig_stream_service = None

    def is_connected(self):
        try:
            self.fetch_account_balance()
            logger.info("IG client is connected.")
            return True

        except Exception as e:
            logger.info(f"Not Connected: {e}. Connecting...")
            return False

    def connect(self):
        self.ig_service.create_session()
        self.ig_service.switch_account(self.acc_number, False)
        self.ig_stream_service = IGStreamService(self.ig_service)
        self.ig_stream_service.create_session()
        atexit.register(self.ig_service.logout)

    def fetch_account_balance(self):
        accounts = self.ig_service.fetch_accounts()
        available_balance = accounts.loc[accounts['accountId'] == self.acc_number, 'available'].values[0]
        return available_balance

    def get_first_open_position(self):
        positions = self.ig_service.fetch_open_positions()
        if not positions.empty:
            return positions.iloc[0].to_dict()
        return None

    def open_position(self, epic: str, direction: str, size: float, stop_distance: float, limit_distance: float):
        result = self.ig_service.create_open_position(
            currency_code="GBP",
            direction=direction,
            epic=epic,
            expiry="DFB",
            order_type="MARKET",
            size=size,
            force_open=True,
            guaranteed_stop=False,
            stop_distance=str(round(stop_distance, 1)),
            trailing_stop=True,
            trailing_stop_increment=10.0,
            limit_distance=str(round(limit_distance, 1)),
            level=None,
            limit_level=None,
            quote_id=None,
            stop_level=None
        )
        logger.info(result)

        deal_ref = result.get("dealReference")

        if deal_ref:
            confirmation = self.ig_service.fetch_deal_by_deal_reference(deal_ref)
            logger.info(confirmation)
            if confirmation.get('dealStatus') == 'ACCEPTED':
                return confirmation

        return None

    def close_position(self, deal_id: str, direction: str, epic: str, size: float):
        # self.ig_service.close_open_position is bugged, so copied here and solved the issue of mutually exclusive dealId and quoteId

        params = {
            "dealId": deal_id,
            "direction": direction,
            "orderType": "MARKET",
            "size": size,
        }

        # Execute request using the library's internal HTTP method
        response = self.ig_service._req(
            action="delete",
            endpoint="/positions/otc",
            params=params,
            session=None,
            version="1"
        )

        if response.status_code == 200:
            deal_reference = json.loads(response.text)["dealReference"]
            return self.ig_service.fetch_deal_by_deal_reference(deal_reference)
        else:
            raise Exception(f"IG close position failed: {response.text}")
