"""SQLite persistence for the simulation state."""
import json
import os
import sqlite3
from server.models import System, Station, AsteroidField, NPCShip

# On fly.io, data dir is a mounted volume. Locally, use project root.
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "game.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.close()


def save_simulation(sim):
    """Serialize and save the full simulation state to SQLite."""
    # Serialize systems
    systems_data = {}
    for sid, sys in sim.universe.items():
        stations = []
        for st in sys.stations:
            stations.append({
                "name": st.name, "system_id": st.system_id,
                "production": st.production, "consumption": st.consumption,
                "inventory": st.inventory, "price_cache": st.price_cache,
            })
        systems_data[sid] = {
            "stations": stations,
        }

    # Serialize ships
    ships_data = []
    for s in sim.ships:
        ships_data.append({
            "id": s.id, "name": s.name, "cargo": s.cargo,
            "cargo_capacity": s.cargo_capacity, "fuel": s.fuel,
            "location": s.location, "destination": s.destination,
            "progress": s.progress, "speed": s.speed, "state": s.state,
        })

    conn = _get_conn()
    conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
                 ("tick_count", str(sim.tick_count)))
    conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
                 ("systems", json.dumps(systems_data)))
    conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
                 ("ships", json.dumps(ships_data)))
    conn.commit()
    conn.close()


def load_simulation(sim) -> bool:
    """Load saved state into an existing simulation. Returns True if state was loaded."""
    if not os.path.exists(DB_PATH):
        return False

    conn = _get_conn()
    init_db()

    row = conn.execute("SELECT value FROM state WHERE key = ?", ("tick_count",)).fetchone()
    if not row:
        conn.close()
        return False

    sim.tick_count = int(row[0])

    # Load systems (only mutable state: station inventories and prices)
    row = conn.execute("SELECT value FROM state WHERE key = ?", ("systems",)).fetchone()
    if row:
        systems_data = json.loads(row[0])
        for sid, data in systems_data.items():
            if sid not in sim.universe:
                continue
            for i, st_data in enumerate(data["stations"]):
                if i < len(sim.universe[sid].stations):
                    sim.universe[sid].stations[i].inventory = st_data["inventory"]
                    sim.universe[sid].stations[i].price_cache = st_data["price_cache"]

    # Load ships
    row = conn.execute("SELECT value FROM state WHERE key = ?", ("ships",)).fetchone()
    if row:
        ships_data = json.loads(row[0])
        sim.ships.clear()
        for sd in ships_data:
            sim.ships.append(NPCShip(
                id=sd["id"], name=sd["name"], cargo=sd["cargo"],
                cargo_capacity=sd["cargo_capacity"], fuel=sd["fuel"],
                location=sd["location"], destination=sd["destination"],
                progress=sd["progress"], speed=sd["speed"], state=sd["state"],
            ))

    conn.close()
    return True


def clear_db():
    """Wipe the database (used by nuke)."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
