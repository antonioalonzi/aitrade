from datetime import datetime

from ai_trader.trade.trade_repository import TradeRepository


def display_index(trade_repository: TradeRepository):
    trades = trade_repository.get_all_trades()

    rows = []
    for trade in trades:
        pnl = trade.profit_or_loss

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

    return {"table_rows": table_rows}

def parse_isodatetime(isodatetime_str: str | None) -> datetime | None:
    return datetime.fromisoformat(isodatetime_str) if isodatetime_str else None

def format_time(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else '-'


