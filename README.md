## 🎯 Opis projektu
 
Aplikacja stworzona z myślą o doradcach finansowych obsługujących 20–50 klientów indywidualnych. Zamiast ręcznego sprawdzania notowań i liczenia zysków/strat w Excelu, doradca ma jedno miejsce gdzie widzi aktualne wyniki wszystkich klientów, może zamykać/dodawać pozycję i wygenerować raport XML.
 
---

## 🛠️ Stack technologiczny
 
| Technologia | Wersja | Zastosowanie |
|---|---|---|
| Python | 3.11 | Język bazowy |
| Streamlit | latest | Interfejs użytkownika |
| SQLAlchemy | 2.0 | ORM / warstwa danych |
| SQLite | — | Baza danych |
| Pydantic | v2 | Walidacja danych |
| yfinance | latest | Aktualne ceny akcji |
| Ollama + llama3.2 | latest | Lokalne AI (offline) |
| xml.etree.ElementTree | stdlib | Eksport XML |
 
---
 
## ⚙️ Instalacja
 
### 1. Klonowanie repozytorium
 
```bash
git clone https://github.com/twoj-login/doradca_finansowy.git
cd doradca_finansowy
```
 
### 2. Środowisko wirtualne
 
```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```
 
### 3. Instalacja zależności
 
```bash
pip install -r requirements.txt
```
 
### 4. Ollama (wymagane do rekomendacji AI)
 
Pobierz i zainstaluj Ollama ze strony [ollama.com](https://ollama.com), następnie pobierz model i uruchom serwer:
 
```bash
ollama pull llama3:latest
ollama serve
```

 
### 5. Załadowanie danych testowych
 
```bash
python -m db.seed_loader
```
 
### 6. Uruchomienie aplikacji
 
```bash
streamlit run app.py
```

 
---