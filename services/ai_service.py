import requests
import json
from typing import List

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3:latest"


def build_prompt(client_name: str, summary: dict, positions: List[dict]) -> str:
    open_pos = [p for p in positions if p["status"] == "open"]
    closed_pos = [p for p in positions if p["status"] == "closed"]

    positions_text = ""
    for p in open_pos:
        sign = "+" if p["pnl_pct"] >= 0 else ""
        positions_text += (
            f"  - {p['ticker']} ({p['currency']}): {p['quantity']:g} szt., "
            f"zysk/strata: {sign}{p['pnl_pct']:.1f}% ({sign}{p['pnl_pln']:,.0f} PLN)\n"
        )

    closed_text = ""
    for p in closed_pos:
        sign = "+" if p["pnl_pct"] >= 0 else ""
        closed_text += (
            f"  - {p['ticker']}: {p['quantity']:g} szt., "
            f"zrealizowany zysk/strata: {sign}{p['pnl_pln']:,.0f} PLN\n"
        )

    prompt = f"""Jesteś doświadczonym analitykiem finansowym. Przeanalizuj poniższy portfel inwestycyjny klienta i napisz krótki komentarz składający się z dokładnie 4 zdań po polsku.

Klient: {client_name}

PODSUMOWANIE PORTFELA:
- Wartość portfela: {summary['total_value_pln']:,.0f} PLN
- Zysk niezrealizowany: {summary['unrealized_pnl_pln']:+,.0f} PLN
- Zysk zrealizowany: {summary['realized_pnl_pln']:+,.0f} PLN

OTWARTE POZYCJE:
{positions_text if positions_text else "  Brak otwartych pozycji."}
ZAMKNIĘTE POZYCJE:
{closed_text if closed_text else "  Brak zamkniętych pozycji."}

Napisz komentarz w dokładnie 4 zdaniach:
1. Ogólna ocena kondycji portfela.
2. Wyróżnij najlepszą i najsłabszą pozycję.
3. Oceń dywersyfikację portfela (waluty, liczba spółek).
4. Konkretna rekomendacja dla doradcy (np. co dokupić, co sprzedać, na co zwrócić uwagę).

Odpowiedz wyłącznie tymi 4 zdaniami, bez wstępu, bez nagłówków, bez punktów."""

    return prompt


def get_ai_recommendation(client_name: str, summary: dict, positions: List[dict]) -> str:
    """Call Ollama and return AI recommendation text."""
    prompt = build_prompt(client_name, summary, positions)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 300,
                },
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    except requests.exceptions.ConnectionError:
        return "Nie można połączyć się z Ollama. Upewnij się że serwis jest uruchomiony (`ollama serve`)."
    except requests.exceptions.Timeout:
        return "Przekroczono czas oczekiwania na odpowiedź modelu AI."
    except Exception as e:
        return f"Błąd generowania rekomendacji: {e}"
