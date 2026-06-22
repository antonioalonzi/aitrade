import threading
import logging

from http.server import HTTPServer, BaseHTTPRequestHandler

from storage.storage import Storage

HOST="localhost"
PORT=8080

logger = logging.getLogger("HttpServer")

class HttpServer(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.storage = Storage()

    def do_GET(self):
        trades = self.storage.get_all_trades()

        rows = []
        for trade in trades:
            pnl = trade.get('profit_or_loss')
            pnl_style = ""

            if pnl is not None:
                pnl_style = 'style="color: #00ff00;"' if pnl >= 0 else 'style="color: #ff0000;"'
                pnl_display = f"£{pnl:.2f}"
            else:
                pnl_display = "OPEN"
                pnl_style = 'style="color: #ffff00;"' # Yellow warning for open positions

            # Handle potential None values for open positions gracefully
            open_price = trade.get('open_price', 0.0)
            close_price = trade.get('close_price')
            close_price_display = f"£{close_price:.2f}" if close_price is not None else "-"

            rows.append(f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #333;">{trade.get('id', '-')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #333; color: #fff;">{trade.get('epic', '-')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #333;">{trade.get('amount', 0)}</td>
                <td style="padding: 10px; border-bottom: 1px solid #333;">{trade.get('opened_at', '-')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #333;">£{open_price:.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #333;">{trade.get('closed_at') or '-'}</td>
                <td style="padding: 10px; border-bottom: 1px solid #333;">{close_price_display}</td>
                <td style="padding: 10px; border-bottom: 1px solid #333;" {pnl_style}>{pnl_display}</td>
                <td style="padding: 10px; border-bottom: 1px solid #333; color: #888; font-size: 0.9em;">{trade.get('comments', '')}</td>
            </tr>
            """)
        table_rows = "".join(rows)

        # 3. Assemble the core template shell
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Matrix Core - Ledger</title>
        </head>
        <body style="background: #0a0a0a; color: #00ff00; font-family: monospace; padding: 40px; line-height: 1.6;">
            <h1 style="color: #00ff00; border-bottom: 2px solid #00ff00; padding-bottom: 10px; margin-bottom: 5px;">Matrix Server Core</h1>
            <p style="color: #888; margin-bottom: 30px;">Web server status: <span style="color: #00ff00; font-weight: bold;">RUNNING</span></p>

            <h2 style="color: #fff;">Transaction Ledger</h2>
            <table style="width: 100%; border-collapse: collapse; text-align: left; background: #111;">
                <thead>
                    <tr style="background: #222; color: #00ff00;">
                        <th style="padding: 12px;">ID</th>
                        <th style="padding: 12px;">Epic</th>
                        <th style="padding: 12px;">Amount</th>
                        <th style="padding: 12px;">Opened At</th>
                        <th style="padding: 12px;">Open Price</th>
                        <th style="padding: 12px;">Closed At</th>
                        <th style="padding: 12px;">Close Price</th>
                        <th style="padding: 12px;">P&L</th>
                        <th style="padding: 12px;">System Comments</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows if table_rows else '<tr><td colspan="9" style="padding: 20px; text-align: center; color: #666;">No transactions recorded in matrix.</td></tr>'}
                </tbody>
            </table>
        </body>
        </html>
        """

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

def run_http_server():
    server = HTTPServer((HOST, PORT), HttpServer)
    logger.info(f"Server is running at http://{HOST}:{PORT}")
    server.serve_forever()


def _populate_some_data():
    db = Storage()

    db.save_open_trade(
        id="DIAAAA111111ABC",
        epic="CS.D.NVIDIA.MINI.IP",
        amount=2.5,
        opened_at="2026-06-13 09:00:00",
        open_price=125.40,
        comment="Gemini breakthrough long strategy"
    )

    db.save_open_trade(
        id="DIAAAA111111XYZ",
        epic="CS.D.AMD.MINI.IP",
        amount=4,
        opened_at="2026-06-13 10:00:00",
        open_price=125.40,
        comment="Gemini breakthrough short strategy"
    )
    db.save_trade_as_closed(
        id="DIAAAA111111XYZ",
        closed_at="2026-06-13 11:00:00",
        close_price=128.40,
        profit_or_loss=1
    )
