import logging
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from jinja2 import Environment, FileSystemLoader

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository
from ai_web.controllers.graph import display_graph
from ai_web.controllers.index import display_index
from ai_web.controllers.market_data import get_market_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JINGA2_ENV = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, "templates")))

logger = logging.getLogger(__name__)



class AiTraderHTTPServer(HTTPServer):
    def __init__(self, market_data_repository: MarketDataRepository, trade_repository: TradeRepository, host: str = "0.0.0.0", port: int = 8080):
        self.market_data_repository = market_data_repository
        self.trade_repository = trade_repository
        super().__init__((host, port), AiTraderHttpRequestHandler)
        logger.info(f"Server is running at http://{host}:{port}")

class AiTraderHttpRequestHandler(BaseHTTPRequestHandler):
    server: AiTraderHTTPServer

    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        match parsed_url.path:
            case path if path.startswith("/static/"):
                self.serve_static_file()
            case "/" | "/index.html":
                model = display_index(self.server.market_data_repository, self.server.trade_repository)
                self.return_view("index.html", model)
            case "/graph":
                epic = query_params.get("epic")[0]
                model = display_graph(self.server.market_data_repository, self.server.trade_repository, epic)
                self.return_view("graph.html", model)
            case "/api/market-data":
                epic = query_params.get("epic")[0]
                data = get_market_data(self.server.market_data_repository, epic)
                self.return_js(data)
            case _:
                self.send_error(404, "Asset Not Found")

    def serve_static_file(self):
        relative_path = self.path.lstrip("/")
        file_path = os.path.join(BASE_DIR, relative_path)

        if not os.path.abspath(file_path).startswith(BASE_DIR):
            self.send_error(403, "Access Denied")
            return

        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_response(200)

            if file_path.endswith(".css"):
                self.send_header("Content-Type", "text/css")
            elif file_path.endswith(".js"):
                self.send_header("Content-Type", "application/javascript")

            self.end_headers()

            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "Asset Not Found")

    def return_view(self, template: str, model):
        src = JINGA2_ENV.get_template(template)
        final_html = src.render(**model)

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(final_html.encode('utf-8'))

    def return_js(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data.encode('utf-8'))



def main():
    log_file = Path("./logs/ai_web.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    data_dir = Path(os.getenv("DATA_DIR", "../../data")).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            TimedRotatingFileHandler(
                filename=log_file,
                when="D",
                interval=3,
                backupCount=3,
                encoding="utf-8"
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )

    market_data_repository_bean = MarketDataRepository(str(data_dir / "ai_market_data.db"))
    trade_repository_bean = TradeRepository(str(data_dir / "ai_trades.db"))
    ai_trader_http_server = AiTraderHTTPServer(market_data_repository_bean, trade_repository_bean)
    ai_trader_http_server.serve_forever()

if __name__ == "__main__":
    main()
