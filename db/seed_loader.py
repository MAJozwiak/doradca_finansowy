import json
from datetime import date
from pathlib import Path
from db.database import get_session, init_db
from db.models import Client, Position

SEED_PATH = Path(__file__).parent.parent / "data" / "seed.json"


def load_clients() -> None:
    """Load clients and positions from seed.json.
    - Klienci: ładuje tylko jeśli tabela jest pusta.
    - Pozycje: ładuje tylko jeśli tabela jest pusta (nawet gdy klienci już istnieją).
    """
    init_db()  # tworzy wszystkie tabele jeśli nie istnieją
    session = get_session()

    try:
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # ── Klienci ────────────────────────────────────────────────────────────
        clients_in_db = session.query(Client).count()
        if clients_in_db == 0:
            clients = []
            for c in data["clients"]:
                client = Client(name=c["name"], email=c["email"], phone=c["phone"])
                session.add(client)
                clients.append(client)
            session.flush()
            print(f"Seeded {len(clients)} clients.")
        else:
            # Pobierz istniejących klientów w kolejności id
            clients = session.query(Client).order_by(Client.id).all()
            print(f"Clients already in DB ({clients_in_db}), skipping client seed.")

        # ── Pozycje ────────────────────────────────────────────────────────────
        positions_in_db = session.query(Position).count()
        if positions_in_db == 0:
            count = 0
            for p in data.get("positions", []):
                idx = p["client_index"]
                if idx >= len(clients):
                    continue
                pos = Position(
                    client_id=clients[idx].id,
                    ticker=p["ticker"],
                    quantity=p["quantity"],
                    currency=p["currency"],
                    purchase_price=p["purchase_price"],
                    purchase_date=date.fromisoformat(p["purchase_date"]),
                    status=p["status"],
                    sell_price=p.get("sell_price"),
                    sell_date=date.fromisoformat(p["sell_date"]) if p.get("sell_date") else None,
                )
                session.add(pos)
                count += 1
            print(f"Seeded {count} positions.")
        else:
            print(f"Positions already in DB ({positions_in_db}), skipping position seed.")

        session.commit()

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    load_clients()
