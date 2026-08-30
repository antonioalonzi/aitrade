import logging
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from string import Template

from ai_trader.ai_trader import TradeRepository

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger(__name__)

class AiTraderHTTPServer(HTTPServer):
    def __init__(self, storage: TradeRepository, host: str = "localhost", port: int = 8080):
        self.storage = storage
        super().__init__((host, port), AiTraderHttpRequestHandler)
        logger.info(f"Server is running at http://{host}:{port}")

class AiTraderHttpRequestHandler(BaseHTTPRequestHandler):
    server: AiTraderHTTPServer

    def do_GET(self):
        match self.path:
            case path if path.startswith("/static/"):
                self.serve_static_file()
            case "/" | "/index.html":
                self.display_index("index.html")
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

    def display_index(self, template: str):
        trades = self.server.storage.get_all_trades()

        rows = []
        for trade in trades:
            pnl = trade.profit_or_loss
            pnl_class = ""

            if pnl is not None:
                pnl_class = 'pnl-profit' if pnl >= 0 else 'pnl-loss'
                pnl_display = f"£{pnl:.2f}"
            else:
                pnl_display = "OPEN"
                pnl_class = 'pnl-open'

            open_price = trade.open_price
            close_price = trade.close_price
            close_price_display = f"£{close_price:.2f}" if close_price is not None else "-"
            opened_at = parse_isodatetime(trade.opened_at)
            closed_at = parse_isodatetime(trade.closed_at)

            rows.append(f"""
            <tr>
                <td>{trade.id}</td>
                <td>{trade.direction}</td>
                <td>{trade.epic}</td>
                <td>{trade.amount}</td>
                <td>{trade.size}</td>
                <td>{format_time(opened_at)}</td>
                <td>£{open_price:.2f}</td>
                <td>{format_time(closed_at)}</td>
                <td>{close_price_display}</td>
                <td class="{pnl_class}">{pnl_display}</td>
                <td>{trade.comment}</td>
            </tr>
            """)
        table_rows = "".join(rows)

        data = {"table_rows": table_rows}
        self.return_view(template, data)

    def return_view(self, template: str, data):
        template_path = os.path.join(BASE_DIR, "templates", template)
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        src = Template(template_content)
        final_html = src.substitute(**data)

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(final_html.encode('utf-8'))

def parse_isodatetime(isodatetime_str: str | None) -> datetime | None:
    return datetime.fromisoformat(isodatetime_str) if isodatetime_str else None

def format_time(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else '-'