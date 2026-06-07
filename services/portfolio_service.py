from datetime import datetime, timedelta
from typing import Optional
import yfinance as yf
from sqlalchemy.orm import Session
from db.models import Position, PriceCache

CACHE_TTL_MINUTES = 10


def _get_or_fetch_price(session: Session, ticker: str) -> Optional[float]:
    """Return cached price if fresh, otherwise fetch from yfinance and upsert."""
    cutoff = datetime.utcnow() - timedelta(minutes=CACHE_TTL_MINUTES)
    cached = session.query(PriceCache).filter(PriceCache.ticker == ticker).first()

    if cached and cached.fetched_at > cutoff:
        return cached.price

    try:
        data = yf.Ticker(ticker)
        info = data.fast_info
        price = info.last_price
        currency = (info.currency or "PLN").upper()

        if price is None:
            return cached.price if cached else None

        if cached:
            cached.price = price
            cached.currency = currency
            cached.fetched_at = datetime.utcnow()
        else:
            cached = PriceCache(ticker=ticker, price=price, currency=currency)
            session.add(cached)

        if currency != "PLN":
            _upsert_fx_rate(session, currency)

        session.commit()
        return price

    except Exception:
        return cached.price if cached else None


def _upsert_fx_rate(session: Session, currency: str) -> None:
    """Fetch currency/PLN rate and upsert into price_cache."""
    fx_ticker_str = f"{currency}PLN=X"
    fx_key = f"{currency}/PLN"
    try:
        fx_data = yf.Ticker(fx_ticker_str)
        rate = fx_data.fast_info.last_price
        if rate is None:
            return
        existing = session.query(PriceCache).filter(PriceCache.ticker == fx_key).first()
        if existing:
            existing.price = rate
            existing.fetched_at = datetime.utcnow()
        else:
            session.add(PriceCache(ticker=fx_key, price=rate, currency="PLN"))
    except Exception:
        pass


def get_fx_rate_to_pln(session: Session, currency: str) -> float:
    """Return exchange rate currency -> PLN from cache. Returns 1.0 for PLN."""
    if currency.upper() == "PLN":
        return 1.0
    fx_key = f"{currency.upper()}/PLN"
    cached = session.query(PriceCache).filter(PriceCache.ticker == fx_key).first()
    if cached:
        return cached.price
    _upsert_fx_rate(session, currency.upper())
    session.commit()
    cached = session.query(PriceCache).filter(PriceCache.ticker == fx_key).first()
    return cached.price if cached else 1.0


def get_enriched_positions(session: Session, client_id: int) -> list[dict]:
    """Return all positions enriched with live prices and P&L (PLN)."""
    positions = (
        session.query(Position)
        .filter(Position.client_id == client_id)
        .order_by(Position.status.desc(), Position.purchase_date.desc())
        .all()
    )

    result = []
    for pos in positions:
        fx = get_fx_rate_to_pln(session, pos.currency)

        if pos.status == "open":
            current_price = _get_or_fetch_price(session, pos.ticker)
            if current_price is None:
                current_price = pos.purchase_price
            pnl_per_share = current_price - pos.purchase_price
            pnl_pln = pnl_per_share * pos.quantity * fx
            pnl_pct = (pnl_per_share / pos.purchase_price * 100) if pos.purchase_price else 0
            current_value_pln = current_price * pos.quantity * fx
        else:
            current_price = pos.sell_price
            pnl_per_share = pos.sell_price - pos.purchase_price
            pnl_pln = pnl_per_share * pos.quantity * fx
            pnl_pct = (pnl_per_share / pos.purchase_price * 100) if pos.purchase_price else 0
            current_value_pln = pos.sell_price * pos.quantity * fx

        result.append({
            "id": pos.id,
            "ticker": pos.ticker,
            "quantity": pos.quantity,
            "currency": pos.currency,
            "purchase_price": pos.purchase_price,
            "purchase_date": pos.purchase_date,
            "current_price": current_price,
            "status": pos.status,
            "sell_price": pos.sell_price,
            "sell_date": pos.sell_date,
            "pnl_pln": pnl_pln,
            "pnl_pct": pnl_pct,
            "current_value_pln": current_value_pln,
            "fx_rate": fx,
        })

    return result


def get_client_summary(session: Session, client_id: int) -> dict:
    """Return total portfolio value, unrealized and realized P&L in PLN."""
    positions = get_enriched_positions(session, client_id)
    total_value = sum(p["current_value_pln"] for p in positions if p["status"] == "open")
    unrealized = sum(p["pnl_pln"] for p in positions if p["status"] == "open")
    realized = sum(p["pnl_pln"] for p in positions if p["status"] == "closed")
    return {
        "total_value_pln": total_value,
        "unrealized_pnl_pln": unrealized,
        "realized_pnl_pln": realized,
    }


def close_position(session: Session, position_id: int, sell_price: float, sell_date) -> None:
    """Mark a position as fully closed."""
    pos = session.query(Position).get(position_id)
    if not pos or pos.status == "closed":
        raise ValueError("Pozycja nie istnieje lub jest już zamknięta.")
    pos.status = "closed"
    pos.sell_price = sell_price
    pos.sell_date = sell_date
    session.commit()


def close_position_partial(
    session: Session,
    position_id: int,
    sell_quantity: float,
    sell_price: float,
    sell_date,
) -> None:
    """
    Partially close a position:
    - Original record: quantity reduced to remaining, stays open
    - New record: sold quantity, status closed
    """
    pos = session.query(Position).get(position_id)
    if not pos or pos.status == "closed":
        raise ValueError("Pozycja nie istnieje lub jest już zamknięta.")
    if sell_quantity >= pos.quantity:
        raise ValueError("Ilość do sprzedaży musi być mniejsza niż posiadana.")

    closed = Position(
        client_id=pos.client_id,
        ticker=pos.ticker,
        quantity=sell_quantity,
        currency=pos.currency,
        purchase_price=pos.purchase_price,
        purchase_date=pos.purchase_date,
        status="closed",
        sell_price=sell_price,
        sell_date=sell_date,
    )
    session.add(closed)
    pos.quantity = pos.quantity - sell_quantity
    session.commit()
