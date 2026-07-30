class MarketDataInMemoryInfo:
    def __init__(self) -> None:
        self.data = {}

    def set_info(self, epic: str, info: dict) -> None:
        self.data[epic] = info

    def get_info(self, epic: str) -> dict:
        return self.data[epic]
