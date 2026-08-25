import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from string import Template

from trade import trade_repository
from trade.trade import Trade
from trade.trade_repository import TradeRepository

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger(__name__)

class AiTraderHttpServer(BaseHTTPRequestHandler):
    storage: TradeRepository

    def setup(self):
        super().setup()
        host, port = self.server.server_address
        logger.info(f"Server is running at https://{host}:{port}")

    def do_GET(self):
        if self.path.startswith("/static/"):
            self.serve_static_file()
            return

        match self.path:
            case "/" | "/index.html":
                return self.display_index("index.html")
            case _:
                return self.send_error(404, "Asset Not Found")

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
        trades = self.storage.get_all_trades()

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

            rows.append(f"""
            <tr>
                <td>{trade.id}</td>
                <td>{trade.epic}</td>
                <td>{trade.amount}</td>
                <td>{trade.opened_at}</td>
                <td>£{open_price:.2f}</td>
                <td>{trade.closed_at or '-'}</td>
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



def _populate_some_data():
    db = TradeRepository("../data/ai_trader.db")

    db.insert_trade(Trade(
        id="DIAAAA111111ABC",
        epic="CS.D.NVIDIA.MINI.IP",
        amount=2.5,
        opened_at="2026-06-13 09:00:00",
        open_price=125.40,
        comment="Gemini breakthrough long strategy"
    ))

    db.insert_trade(Trade(
        id="DIAAAA111111XYZ",
        epic="CS.D.AMD.MINI.IP",
        amount=4,
        opened_at="2026-06-14 10:00:00",
        open_price=124.40,
        comment="Gemini breakthrough short strategy"
    ))
    db.update_trade(Trade(
        id="DIAAAA111111XYZ",
        closed_at="2026-06-14 11:00:00",
        close_price=125.40,
        profit_or_loss=-1
    ))


    db.insert_trade(Trade(
        id="DIAAAA111111XYY",
        epic="CS.D.AMD.MINI.IP",
        amount=10,
        opened_at="2026-06-14 10:00:00",
        open_price=125.40,
        comment="Gemini breakthrough short strategy"
    ))
    db.update_trade(Trade(
        id="DIAAAA111111XYY",
        closed_at="2026-06-14 11:00:00",
        close_price=120.50,
        profit_or_loss=-5.10
    ))
