import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from db.database import get_session, init_db
from db.models import Client
from db.seed_loader import load_clients
from db.schemas import ClientCreate
from pydantic import ValidationError

st.set_page_config(
    page_title="Klienci | Doradca",
    page_icon="👥",
    layout="wide",
)

init_db()
load_clients()

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

if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_client_id" not in st.session_state:
    st.session_state.edit_client_id = None
if "delete_confirm_id" not in st.session_state:
    st.session_state.delete_confirm_id = None

st.markdown('<div class="top-accent"></div>', unsafe_allow_html=True)
st.markdown('<div class="page-title">Baza Klientów</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Panel doradcy finansowego</div>', unsafe_allow_html=True)

col_s1, col_s2, col_btn = st.columns([2, 2, 1])
with col_s1:
    search_name = st.text_input("Szukaj po imieniu", placeholder="np. Marek", key="search_name")
with col_s2:
    search_surname = st.text_input("Szukaj po nazwisku", placeholder="np. Kowalski", key="search_surname")
with col_btn:
    st.markdown("<div style='height:1.95rem'></div>", unsafe_allow_html=True)
    if st.button("＋ Dodaj klienta", use_container_width=True):
        st.session_state.show_add_form = not st.session_state.show_add_form
        st.session_state.edit_client_id = None

if st.session_state.show_add_form:
    with st.container(border=True):
        st.markdown("**Nowy klient**")
        c1, c2, c3 = st.columns(3)
        with c1:
            new_name = st.text_input("Imię i nazwisko", key="new_name")
        with c2:
            new_email = st.text_input("Email", key="new_email")
        with c3:
            new_phone = st.text_input("Telefon", key="new_phone")

        btn_save, btn_cancel, _ = st.columns([1, 1, 5])
        with btn_save:
            if st.button("Zapisz", type="primary", use_container_width=True):
                if new_name and new_email and new_phone:
                    try:
                        validated = ClientCreate(name=new_name, email=new_email, phone=new_phone)
                        db = get_session()
                        client = Client(name=validated.name, email=str(validated.email), phone=validated.phone)
                        db.add(client)
                        db.commit()
                        db.close()
                        st.success("Klient dodany.")
                        st.session_state.show_add_form = False
                        st.rerun()
                    except ValidationError as ve:
                        for err in ve.errors():
                            st.error(f"{err['msg']}")
                    except Exception as e:
                        st.error(f"Błąd: {e}")
                else:
                    st.warning("Wypełnij wszystkie pola.")
        with btn_cancel:
            if st.button("Anuluj", use_container_width=True):
                st.session_state.show_add_form = False
                st.rerun()

st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

session = get_session()
query = session.query(Client).order_by(Client.name)
if search_name.strip():
    query = query.filter(Client.name.ilike(f"%{search_name.strip()}%"))
if search_surname.strip():
    query = query.filter(Client.name.ilike(f"%{search_surname.strip()}%"))
clients = query.all()

st.markdown(f'<div class="result-count">{len(clients)} klientów</div>', unsafe_allow_html=True)

cols_h = st.columns([3, 3, 2, 1.2, 0.8, 0.8])
for col, label in zip(cols_h, ["Klient", "Email", "Telefon", "Portfel", "", ""]):
    col.markdown(
        f"<span style='font-size:0.8rem;font-weight:600;color:#8a93ab;"
        f"text-transform:uppercase;letter-spacing:0.08em'>{label}</span>",
        unsafe_allow_html=True,
    )

st.markdown("<hr style='border:none;border-top:1.5px solid #dde2ef;margin:0.4rem 0 0.5rem 0'>", unsafe_allow_html=True)

if not clients:
    st.markdown("<p style='color:#8a93ab;font-size:0.9rem;padding:1rem 0'>Brak wyników.</p>", unsafe_allow_html=True)
else:
    for client in clients:
        cols = st.columns([3, 3, 2, 1.2, 0.8, 0.8])

        with cols[0]:
            st.markdown(f"<span class='cli-name'>{client.name}</span>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"<span class='cli-email'>{client.email}</span>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"<span class='cli-phone'>{client.phone}</span>", unsafe_allow_html=True)
        with cols[3]:
            if st.button("Otwórz →", key=f"port_{client.id}", use_container_width=True):
                st.session_state["selected_client_id"] = client.id
                st.session_state["selected_client_name"] = client.name
                st.query_params["client_id"] = str(client.id)
                st.switch_page("pages/02_portfel.py")
        with cols[4]:
            if st.button("Edytuj", key=f"edit_{client.id}", use_container_width=True):
                st.session_state.edit_client_id = client.id
                st.session_state.delete_confirm_id = None
                st.session_state.show_add_form = False
        with cols[5]:
            if st.button("Usuń", key=f"del_{client.id}", use_container_width=True):
                st.session_state.delete_confirm_id = client.id
                st.session_state.edit_client_id = None

        if st.session_state.edit_client_id == client.id:
            with st.container(border=True):
                st.markdown(f"**Edytuj: {client.name}**")
                e1, e2, e3 = st.columns(3)
                with e1:
                    e_name = st.text_input("Imię i nazwisko", value=client.name, key=f"ename_{client.id}")
                with e2:
                    e_email = st.text_input("Email", value=client.email, key=f"eemail_{client.id}")
                with e3:
                    e_phone = st.text_input("Telefon", value=client.phone, key=f"ephone_{client.id}")
                sb, cb, _ = st.columns([1, 1, 5])
                with sb:
                    if st.button("Zapisz zmiany", type="primary", key=f"esave_{client.id}", use_container_width=True):
                        try:
                            validated = ClientCreate(name=e_name, email=e_email, phone=e_phone)
                            db = get_session()
                            c = db.query(Client).get(client.id)
                            c.name = validated.name
                            c.email = str(validated.email)
                            c.phone = validated.phone
                            db.commit()
                            db.close()
                            st.session_state.edit_client_id = None
                            st.rerun()
                        except ValidationError as ve:
                            for err in ve.errors():
                                st.error(f"❌ {err['msg']}")
                        except Exception as e:
                            st.error(f"Błąd: {e}")
                with cb:
                    if st.button("Anuluj", key=f"ecancel_{client.id}", use_container_width=True):
                        st.session_state.edit_client_id = None
                        st.rerun()

        if st.session_state.delete_confirm_id == client.id:
            with st.container(border=True):
                st.warning(f"Czy na pewno chcesz usunąć **{client.name}**? Operacji nie można cofnąć.")
                dc1, dc2, _ = st.columns([1, 1, 5])
                with dc1:
                    if st.button("Tak, usuń", type="primary", key=f"dconfirm_{client.id}", use_container_width=True):
                        try:
                            db = get_session()
                            c = db.query(Client).get(client.id)
                            db.delete(c)
                            db.commit()
                            db.close()
                            st.session_state.delete_confirm_id = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Błąd: {e}")
                with dc2:
                    if st.button("Anuluj", key=f"dcancel_{client.id}", use_container_width=True):
                        st.session_state.delete_confirm_id = None
                        st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid #edf0f7;margin:0.2rem 0'>", unsafe_allow_html=True)

session.close()
