import xml.etree.ElementTree as ET
from datetime import date
from typing import List


def generate_portfolio_xml(
    client: dict,
    summary: dict,
    positions: List[dict],
) -> str:
    """Generate XML report for a client portfolio."""

    root = ET.Element("raport")

    # ── Klient ─────────────────────────────────────────────────────────────────
    klient_el = ET.SubElement(root, "klient")
    ET.SubElement(klient_el, "id").text = str(client["id"])
    ET.SubElement(klient_el, "nazwa").text = client["name"]
    ET.SubElement(klient_el, "email").text = client["email"]
    ET.SubElement(klient_el, "telefon").text = client["phone"]
    ET.SubElement(klient_el, "data_wygenerowania").text = date.today().isoformat()

    # ── Podsumowanie ───────────────────────────────────────────────────────────
    summary_el = ET.SubElement(root, "podsumowanie")
    ET.SubElement(summary_el, "wartosc_portfela_pln").text = f"{summary['total_value_pln']:.2f}"
    ET.SubElement(summary_el, "zysk_niezrealizowany_pln").text = f"{summary['unrealized_pnl_pln']:.2f}"
    ET.SubElement(summary_el, "zysk_zrealizowany_pln").text = f"{summary['realized_pnl_pln']:.2f}"

    # ── Pozycje ────────────────────────────────────────────────────────────────
    pozycje_el = ET.SubElement(root, "pozycje")
    for p in positions:
        poz = ET.SubElement(pozycje_el, "pozycja")
        ET.SubElement(poz, "ticker").text = p["ticker"]
        ET.SubElement(poz, "ilosc").text = str(p["quantity"])
        ET.SubElement(poz, "cena_zakupu").text = f"{p['purchase_price']:.2f}"
        ET.SubElement(poz, "cena_aktualna").text = f"{p['current_price']:.2f}" if p["current_price"] else "—"
        ET.SubElement(poz, "waluta").text = p["currency"]
        ET.SubElement(poz, "kurs_do_pln").text = f"{p['fx_rate']:.4f}"
        ET.SubElement(poz, "zysk_strata_pln").text = f"{p['pnl_pln']:.2f}"
        ET.SubElement(poz, "zysk_strata_pct").text = f"{p['pnl_pct']:.2f}"
        ET.SubElement(poz, "status").text = p["status"]
        ET.SubElement(poz, "data_zakupu").text = p["purchase_date"].isoformat() if p["purchase_date"] else ""
        if p["status"] == "closed":
            ET.SubElement(poz, "cena_sprzedazy").text = f"{p['sell_price']:.2f}" if p["sell_price"] else ""
            ET.SubElement(poz, "data_sprzedazy").text = p["sell_date"].isoformat() if p["sell_date"] else ""

    # ── Pretty print ───────────────────────────────────────────────────────────
    _indent(root)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=False)


def _indent(elem, level=0):
    """Add indentation for readable XML output (fallback for older Python)."""
    indent = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            _indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent