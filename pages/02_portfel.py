import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date
from db.database import get_session, init_db
from db.models import Client, Position
from services.portfolio_service import (
    get_enriched_positions,
    get_client_summary,
    close_position,
    close_position_partial,
)
from services.ai_service import get_ai_recommendation
from services.xml_export import generate_portfolio_xml
from db.schemas import PositionCreate
from pydantic import ValidationError

st.set_page_config(page_title="Portfel | Doradca", page_icon="📈", layout="wide")

init_db()

# ── Guard: restore from query params on refresh ────────────────────────────────
from db.models import Client as _Client

_params = st.query_params
if "client_id" in _params and "selected_client_id" not in st.session_state:
    try:
        _cid = int(_params["client_id"])
        _db = get_session()
        _c = _db.query(_Client).get(_cid)
        if _c:
            st.session_state["selected_client_id"] = _c.id
            st.session_state["selected_client_name"] = _c.name
        _db.close()
    except Exception:
        pass

if "selected_client_id" not in st.session_state:
    st.warning("Nie wybrano klienta.")
    if st.button("← Wróć do bazy klientów"):
        st.switch_page("pages/01_klienci.py")
    st.stop()

client_id = st.session_state["selected_client_id"]
client_name = st.session_state.get("selected_client_name", "")
st.query_params["client_id"] = str(client_id)

# ── CSS ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Sora', sans-serif !important;
    background-color: #f0f2f8 !important;
    color: #1c2133 !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 3rem !important;
    padding-left: 11rem !important;
    padding-right: 11rem !important;
}

/* ── Top accent bar ── */
.top-accent {
    height: 4px;
    background: linear-gradient(90deg, #4f6ef7 0%, #7c3aed 40%, #0ea5e9 100%);
    border-radius: 2px;
    margin-bottom: 1.8rem;
}

/* ── Page title ── */
.page-title {
    font-size: 1.9rem;
    font-weight: 700;
    color: #1c2133;
    letter-spacing: -0.03em;
    margin-bottom: 0.15rem;
}
.page-subtitle {
    font-size: 0.85rem;
    color: #8a93ab;
    margin-bottom: 1.8rem;
}

/* ── Summary cards ── */
.summary-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
}
.summary-card {
    flex: 1;
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    position: relative;
    overflow: hidden;
}
.summary-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    opacity: 0.08;
    border-radius: 12px;
}
.summary-card.blue   { background: #eef1ff; border: 1.5px solid #c7d2fe; }
.summary-card.green  { background: #f0fdf4; border: 1.5px solid #bbf7d0; }
.summary-card.red    { background: #fef2f2; border: 1.5px solid #fecaca; }
.summary-card.purple { background: #faf5ff; border: 1.5px solid #e9d5ff; }
.summary-card .s-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
}
.summary-card.blue   .s-label { color: #4f6ef7; }
.summary-card.green  .s-label { color: #16a34a; }
.summary-card.red    .s-label { color: #dc2626; }
.summary-card.purple .s-label { color: #7c3aed; }
.summary-card .s-value {
    font-size: 1.45rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}
.summary-card.blue   .s-value { color: #3b5bdb; }
.summary-card.green  .s-value { color: #15803d; }
.summary-card.red    .s-value { color: #b91c1c; }
.summary-card.purple .s-value { color: #6d28d9; }
.summary-card .s-icon {
    position: absolute;
    right: 1rem; top: 50%;
    transform: translateY(-50%);
    font-size: 2rem;
    opacity: 0.15;
}

/* ── Table ── */
.tbl-col-label {
    font-size: 0.76rem;
    font-weight: 600;
    color: #8a93ab;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.ticker-badge {
    display: inline-block;
    background: linear-gradient(135deg, #4f6ef7 0%, #7c3aed 100%);
    color: #fff;
    font-weight: 700;
    font-size: 0.82rem;
    padding: 0.18rem 0.55rem;
    border-radius: 6px;
    letter-spacing: 0.04em;
}
.ticker-badge.closed {
    background: #e2e8f0;
    color: #94a3b8;
}
.pnl-positive { color: #15803d; font-weight: 600; font-size: 0.9rem; }
.pnl-negative { color: #b91c1c; font-weight: 600; font-size: 0.9rem; }
.status-open {
    display: inline-block;
    background: #dcfce7;
    color: #15803d;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.15rem 0.5rem;
    border-radius: 20px;
    border: 1px solid #bbf7d0;
}
.status-closed {
    display: inline-block;
    background: #f1f5f9;
    color: #94a3b8;
    font-size: 0.75rem;
    font-weight: 500;
    padding: 0.15rem 0.5rem;
    border-radius: 20px;
    border: 1px solid #e2e8f0;
}

/* ── Inputs ── */
.stTextInput > label, .stNumberInput > label,
.stDateInput > label, .stSelectbox > label {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: #8a93ab !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #ffffff !important;
    border: 1.5px solid #dde2ef !important;
    border-radius: 8px !important;
    color: #1c2133 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.9rem !important;
    box-shadow: 0 1px 3px rgba(60,80,140,0.05) !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #4f6ef7 !important;
    box-shadow: 0 0 0 3px rgba(79,110,247,0.12) !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'Sora', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    border: 1.5px solid #dde2ef !important;
    background: #ffffff !important;
    color: #5a6380 !important;
    transition: all 0.15s !important;
    box-shadow: 0 1px 3px rgba(60,80,140,0.06) !important;
}
.stButton > button:hover {
    border-color: #4f6ef7 !important;
    color: #4f6ef7 !important;
    background: #f0f3ff !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4f6ef7 0%, #7c3aed 100%) !important;
    border: none !important;
    color: #fff !important;
    box-shadow: 0 3px 10px rgba(79,110,247,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 14px rgba(79,110,247,0.45) !important;
    transform: translateY(-1px) !important;
}

/* ── Section label ── */
.section-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #8a93ab;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── AI card ── */
.ai-card {
    background: linear-gradient(135deg, #f0f3ff 0%, #faf5ff 100%);
    border: 1.5px solid #c7d2fe;
    border-left: 4px solid #4f6ef7;
    border-radius: 12px;
    padding: 1.3rem 1.6rem;
    font-size: 0.95rem;
    line-height: 1.8;
    color: #1c2133;
}

/* ── XML box ── */
.xml-box {
    background: #1e1b4b;
    border-radius: 12px;
    padding: 1.5rem;
    overflow-x: auto;
    font-family: 'Courier New', monospace;
    font-size: 0.82rem;
    line-height: 1.6;
    color: #e8eaf0;
    border: 1.5px solid #3730a3;
    white-space: pre;
    max-height: 520px;
    overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ───────────────────────────────────────────────────────────────
if "show_add_position" not in st.session_state:
    st.session_state.show_add_position = False
if "close_position_id" not in st.session_state:
    st.session_state.close_position_id = None

# ── Header row ──────────────────────────────────────────────────────────────────
col_title, col_btns = st.columns([5, 2])
st.markdown('<div class="top-accent"></div>', unsafe_allow_html=True)
with col_title:
    st.markdown(f'<div class="page-title">{client_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Portfel inwestycyjny</div>', unsafe_allow_html=True)
# buttons rendered after data load below

st.markdown("<hr style='border:none;border-top:1.5px solid #dde2ef;margin:0.5rem 0 1.5rem 0'>", unsafe_allow_html=True)

# ── Load data ───────────────────────────────────────────────────────────────────
session = get_session()

with st.spinner("Pobieranie aktualnych cen..."):
    summary = get_client_summary(session, client_id)
    positions = get_enriched_positions(session, client_id)

# ── Download XML (rendered here so data is available) ───────────────────────────
db_client_r = session.query(Client).get(client_id)
client_dict_r = {"id": db_client_r.id, "name": db_client_r.name,
                 "email": db_client_r.email, "phone": db_client_r.phone}
xml_bytes = generate_portfolio_xml(client_dict_r, summary, positions).encode("utf-8")
filename_r = f"raport_{client_name.replace(' ', '_')}.xml"
with col_btns:
    b1_dl, b2_dl = st.columns(2)
    with b1_dl:
        if st.button("← Klienci", key="back_btn", use_container_width=True):
            st.switch_page("pages/01_klienci.py")
    with b2_dl:
        st.download_button(
            label="Raport XML",
            data=xml_bytes,
            file_name=filename_r,
            mime="application/xml",
            use_container_width=True,
        )

# ── Summary cards ───────────────────────────────────────────────────────────────
unreal = summary["unrealized_pnl_pln"]
real = summary["realized_pnl_pln"]
total = summary["total_value_pln"]

unreal_cls = "positive" if unreal >= 0 else "negative"
real_cls   = "positive" if real >= 0 else "negative"
unreal_sign = "+" if unreal >= 0 else ""
real_sign   = "+" if real >= 0 else ""

st.markdown(f"""
<div class="summary-row">
    <div class="summary-card blue">
        <div class="s-label">Wartość portfela</div>
        <div class="s-value">{total:,.0f} PLN</div>
    </div>
    <div class="summary-card {'green' if unreal >= 0 else 'red'}">
        <div class="s-label">Zysk niezrealizowany</div>
        <div class="s-value">{unreal_sign}{unreal:,.0f} PLN</div>
    </div>
    <div class="summary-card {'green' if real >= 0 else 'red'}">
        <div class="s-label">Zysk zrealizowany</div>
        <div class="s-value">{real_sign}{real:,.0f} PLN</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Add position button & form ──────────────────────────────────────────────────
col_sec, col_add = st.columns([5, 1])
with col_sec:
    st.markdown(
        "<span style='font-size:0.78rem;font-weight:600;color:#8a93ab;"
        "text-transform:uppercase;letter-spacing:0.08em'>Instrumenty</span>",
        unsafe_allow_html=True,
    )
with col_add:
    if st.button("＋ Dodaj pozycję", use_container_width=True):
        st.session_state.show_add_position = not st.session_state.show_add_position
        st.session_state.close_position_id = None
        # Reset ticker state when opening fresh
        if st.session_state.show_add_position:
            st.session_state.pop("verified_ticker", None)
            st.session_state.pop("verified_currency", None)
            st.session_state.pop("ticker_verified", None)
            st.session_state.pop("new_ticker", None)

if st.session_state.show_add_position:
    with st.container(border=True):
        st.markdown("**Nowa pozycja**")

        # Step 1: ticker input + validate button (only when not yet verified)
        if not st.session_state.get("ticker_verified"):
            t1, t2, _ = st.columns([2, 1, 4])
            with t1:
                new_ticker = st.text_input("Ticker", placeholder="np. AAPL", key="new_ticker").upper().strip()
            with t2:
                st.markdown("<div style='height:1.95rem'></div>", unsafe_allow_html=True)
                check_btn = st.button("Sprawdź ticker", use_container_width=True, key="check_ticker")

            if check_btn:
                if new_ticker:
                    try:
                        import yfinance as yf
                        info = yf.Ticker(new_ticker).fast_info
                        price = info.last_price
                        currency = (info.currency or "").upper()
                        if price and currency:
                            st.session_state["verified_ticker"] = new_ticker
                            st.session_state["verified_currency"] = currency
                            st.session_state["ticker_verified"] = True
                            st.rerun()
                        else:
                            st.error("Nie znaleziono tickera. Sprawdź pisownię.")
                    except Exception as e:
                        st.error(f"Błąd weryfikacji: {e}")
                else:
                    st.warning("Wpisz ticker przed sprawdzeniem.")

        # Step 2: form shown only after successful verification
        else:
            cur = st.session_state["verified_currency"]
            ticker = st.session_state["verified_ticker"]

            hc1, hc2 = st.columns([4, 1])
            with hc1:
                st.markdown(
                    f"<span style='font-size:0.9rem;font-weight:600;color:#1c2133'>Ticker: {ticker}</span>"
                    f"&nbsp;&nbsp;<span style='font-size:0.82rem;color:#5a6380'>Waluta: <strong>{cur}</strong></span>",
                    unsafe_allow_html=True,
                )
            with hc2:
                if st.button("↩ Resetuj ticker", use_container_width=True, key="reset_ticker"):
                    st.session_state.pop("verified_ticker", None)
                    st.session_state.pop("verified_currency", None)
                    st.session_state.pop("ticker_verified", None)
                    st.session_state.pop("new_ticker", None)
                    st.rerun()
            st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)

            f1, f2, f3 = st.columns(3)
            with f1:
                new_qty = st.number_input("Liczba akcji", min_value=0.0001, step=1.0, key="new_qty")
            with f2:
                new_price = st.number_input("Cena zakupu", min_value=0.0001, step=0.01, key="new_price")
            with f3:
                new_date = st.date_input("Data zakupu", value=date.today(), key="new_date")

            bs, bc, _ = st.columns([1, 1, 5])
            with bs:
                if st.button("Zapisz", type="primary", use_container_width=True, key="save_pos"):
                    try:
                        validated = PositionCreate(
                            ticker=ticker,
                            quantity=new_qty,
                            currency=cur,
                            purchase_price=new_price,
                            purchase_date=new_date,
                        )
                        db = get_session()
                        pos = Position(
                            client_id=client_id,
                            ticker=validated.ticker,
                            quantity=validated.quantity,
                            currency=validated.currency.value,
                            purchase_price=validated.purchase_price,
                            purchase_date=validated.purchase_date,
                            status="open",
                        )
                        db.add(pos)
                        db.commit()
                        db.close()
                        st.session_state.pop("verified_ticker", None)
                        st.session_state.pop("verified_currency", None)
                        st.session_state.pop("ticker_verified", None)
                        st.session_state.show_add_position = False
                        st.rerun()
                    except ValidationError as ve:
                        for err in ve.errors():
                            st.error(f"❌ {err['msg']}")
                    except Exception as e:
                        st.error(f"Błąd: {e}")
            with bc:
                if st.button("Anuluj", use_container_width=True, key="cancel_pos"):
                    st.session_state.pop("verified_ticker", None)
                    st.session_state.pop("verified_currency", None)
                    st.session_state.pop("ticker_verified", None)
                    st.session_state.show_add_position = False
                    st.rerun()

st.markdown("<hr style='border:none;border-top:1.5px solid #dde2ef;margin:0.5rem 0 0.6rem 0'>", unsafe_allow_html=True)

# ── Table header ────────────────────────────────────────────────────────────────
COLS = [1.2, 0.9, 1.1, 1.1, 0.8, 1.3, 1.3, 0.9, 1.5]
hdrs = ["Ticker", "Liczba", "Cena zakupu", "Cena aktualna", "Waluta",
        "Zysk/Strata PLN", "Zysk/Strata %", "Status", "Akcja"]

h_cols = st.columns(COLS)
for col, lbl in zip(h_cols, hdrs):
    col.markdown(f"<span class='tbl-col-label'>{lbl}</span>", unsafe_allow_html=True)

st.markdown("<hr style='border:none;border-top:1px solid #edf0f7;margin:0.3rem 0 0.4rem 0'>", unsafe_allow_html=True)

# ── Rows ─────────────────────────────────────────────────────────────────────────
if not positions:
    st.markdown("<p style='color:#8a93ab;font-size:0.9rem;padding:1rem 0'>Brak pozycji.</p>", unsafe_allow_html=True)

for p in positions:
    is_open = p["status"] == "open"
    pnl = p["pnl_pln"]
    pnl_pct = p["pnl_pct"]
    pnl_cls = "pnl-positive" if pnl >= 0 else "pnl-negative"
    pnl_sign = "+" if pnl >= 0 else ""
    row_opacity = "1" if is_open else "0.55"

    row_cols = st.columns(COLS)

    with row_cols[0]:
        badge_cls = "ticker-badge" if is_open else "ticker-badge closed"
        st.markdown(f"<span class='{badge_cls}'>{p['ticker']}</span>", unsafe_allow_html=True)
    with row_cols[1]:
        st.markdown(f"<span style='opacity:{row_opacity}'>{p['quantity']:g}</span>", unsafe_allow_html=True)
    with row_cols[2]:
        st.markdown(f"<span style='opacity:{row_opacity}'>{p['purchase_price']:,.2f}</span>", unsafe_allow_html=True)
    with row_cols[3]:
        cp = p['current_price']
        st.markdown(f"<span style='opacity:{row_opacity}'>{cp:,.2f}</span>" if cp else "—", unsafe_allow_html=True)
    with row_cols[4]:
        st.markdown(f"<span style='opacity:{row_opacity};font-size:0.85rem;color:#5a6380'>{p['currency']}</span>", unsafe_allow_html=True)
    with row_cols[5]:
        st.markdown(f"<span class='{pnl_cls}' style='opacity:{row_opacity}'>{pnl_sign}{pnl:,.0f} PLN</span>", unsafe_allow_html=True)
    with row_cols[6]:
        st.markdown(f"<span class='{pnl_cls}' style='opacity:{row_opacity}'>{pnl_sign}{pnl_pct:.1f}%</span>", unsafe_allow_html=True)
    with row_cols[7]:
        status_lbl = "● Otwarta" if is_open else "✓ Zamknięta"
        status_cls = "status-open" if is_open else "status-closed"
        st.markdown(f"<span class='{status_cls}'>{status_lbl}</span>", unsafe_allow_html=True)
    with row_cols[8]:
        if is_open:
            if st.button("Zamknij pozycję", key=f"close_{p['id']}", use_container_width=True):
                st.session_state.close_position_id = p["id"]
                st.session_state.show_add_position = False
        else:
            sell_d = p['sell_date'].strftime('%d.%m.%Y') if p['sell_date'] else "—"
            st.markdown(f"<span style='font-size:0.78rem;color:#8a93ab'>Sprzedano {sell_d}</span>", unsafe_allow_html=True)

    # ── Close position form ─────────────────────────────────────────────────────
    if st.session_state.close_position_id == p["id"]:
        with st.container(border=True):
            sell_price = p["current_price"] or p["purchase_price"]
            sell_date = date.today()
            st.markdown(
                f"**Zamknij pozycję: {p['ticker']}** — posiadasz {p['quantity']:g} szt. &nbsp;|&nbsp; "
                f"Cena rynkowa: **{sell_price:,.2f} {p['currency']}** &nbsp;|&nbsp; "
                f"Data sprzedaży: **{sell_date.strftime('%d.%m.%Y')}**"
            )
            cl1, _ = st.columns([1, 3])
            with cl1:
                sell_qty = st.number_input(
                    "Liczba do sprzedaży",
                    min_value=0.0001,
                    max_value=float(p["quantity"]),
                    value=float(p["quantity"]),
                    step=1.0,
                    key=f"sell_qty_{p['id']}",
                )

            csb, ccb, _ = st.columns([1, 1, 5])
            with csb:
                if st.button("Potwierdź sprzedaż", type="primary", key=f"confirm_close_{p['id']}", use_container_width=True):
                    try:
                        db = get_session()
                        if sell_qty >= p["quantity"]:
                            close_position(db, p["id"], sell_price, sell_date)
                        else:
                            close_position_partial(db, p["id"], sell_qty, sell_price, sell_date)
                        db.close()
                        st.success("Pozycja zamknięta.")
                        st.session_state.close_position_id = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd: {e}")
            with ccb:
                if st.button("Anuluj", key=f"cancel_close_{p['id']}", use_container_width=True):
                    st.session_state.close_position_id = None
                    st.rerun()

    st.markdown("<hr style='border:none;border-top:1px solid #edf0f7;margin:0.2rem 0'>", unsafe_allow_html=True)

# ── Wykres portfela ─────────────────────────────────────────────────────────────
open_positions = [p for p in positions if p["status"] == "open"]

if open_positions:
    st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)
    st.markdown(
        "<span style='font-size:0.78rem;font-weight:600;color:#8a93ab;"
        "text-transform:uppercase;letter-spacing:0.08em'>Skład portfela (otwarte pozycje)</span>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border:none;border-top:1.5px solid #dde2ef;margin:0.4rem 0 1rem 0'>", unsafe_allow_html=True)

    chart_col, legend_col = st.columns([2, 1])

    import json as _json
    labels = [p["ticker"] for p in open_positions]
    values = [round(p["current_value_pln"], 2) for p in open_positions]
    palette = [
        "#4f6ef7","#7c3aed","#0ea5e9","#10b981","#f59e0b",
        "#ef4444","#ec4899","#14b8a6","#8b5cf6","#f97316",
    ]
    colors = (palette * ((len(labels) // len(palette)) + 1))[:len(labels)]
    pie_data = _json.dumps({"labels": labels, "values": values, "colors": colors})

    with chart_col:
        html_chart = (
            '<div style="display:flex;justify-content:center;align-items:center;height:300px;">'
            '<canvas id="pieChart" width="300" height="300"></canvas>'
            '</div>'
            '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>'
            '<script>'
            'const d = ' + pie_data + ';'
            'new Chart(document.getElementById("pieChart"), {'
            '  type: "doughnut",'
            '  data: {'
            '    labels: d.labels,'
            '    datasets: [{'
            '      data: d.values,'
            '      backgroundColor: d.colors,'
            '      borderColor: "#f4f6fb",'
            '      borderWidth: 3,'
            '      hoverOffset: 8'
            '    }]'
            '  },'
            '  options: {'
            '    responsive: false,'
            '    plugins: {'
            '      legend: { display: false },'
            '      tooltip: { callbacks: { label: (ctx) => " " + ctx.label + ": " + ctx.parsed.toLocaleString("pl-PL") + " PLN" } }'
            '    },'
            '    cutout: "60%"'
            '  }'
            '});'
            '</script>'
        )
        st.components.v1.html(html_chart, height=320)

    with legend_col:
        total_val = sum(values)
        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
        for i, p in enumerate(open_positions):
            pct = (p["current_value_pln"] / total_val * 100) if total_val else 0
            color = colors[i]
            pnl_sign = "+" if p["pnl_pln"] >= 0 else ""
            pnl_color = "#16a34a" if p["pnl_pln"] >= 0 else "#dc2626"
            st.markdown(
                "<div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.65rem'>"
                "<div style='width:12px;height:12px;border-radius:3px;background:" + color + ";flex-shrink:0'></div>"
                "<div>"
                "<span style='font-weight:600;font-size:0.88rem;color:#1c2133'>" + p["ticker"] + "</span>"
                "<span style='font-size:0.78rem;color:#8a93ab;margin-left:0.4rem'>" + f"{pct:.1f}%" + "</span><br>"
                "<span style='font-size:0.78rem;color:#5a6380'>" + f"{p['current_value_pln']:,.0f} PLN" + "</span>"
                "&nbsp;<span style='font-size:0.75rem;color:" + pnl_color + "'>" + f"{pnl_sign}{p['pnl_pln']:,.0f}" + "</span>"
                "</div></div>",
                unsafe_allow_html=True,
            )

# ── AI Rekomendacja ───────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)
st.markdown(
    "<span style='font-size:0.78rem;font-weight:600;color:#8a93ab;"
    "text-transform:uppercase;letter-spacing:0.08em'>Rekomendacja AI</span>",
    unsafe_allow_html=True,
)
st.markdown("<hr style='border:none;border-top:1.5px solid #dde2ef;margin:0.4rem 0 1rem 0'>", unsafe_allow_html=True)

with st.spinner('Ollama analizuje portfel...'):
    ai_text = get_ai_recommendation(client_name, summary, positions)

card_style = (
    ''
)
st.markdown(
    '<div class="ai-card">' + ai_text + '</div>',
    unsafe_allow_html=True,
)

session.close()
