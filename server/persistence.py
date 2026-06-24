"""SQLite persistence for the simulation state."""
import json
import os
import sqlite3
from server.models import NPCShip

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
    systems_data = {}
    for sid, sys in sim.universe.items():
        stations = []
        for st in sys.stations:
            stations.append({
                "name": st.name, "system_id": st.system_id,
                "station_type": st.station_type, "produces": st.produces,
                "inventory": st.inventory, "price_cache": st.price_cache,
                "production_rate": st.production_rate,
            })
        systems_data[sid] = {"stations": stations}

    ships_data = []
    for s in sim.ships:
        ships_data.append({
            "id": s.id, "name": s.name, "cargo": s.cargo,
            "cargo_capacity": s.cargo_capacity, "fuel": s.fuel,
            "location": s.location, "destination": s.destination,
            "progress": s.progress, "speed": s.speed, "state": s.state,
            "state_timer": s.state_timer, "role": s.role,
            "ship_class": s.ship_class, "route_path": s.route_path,
            "faction": s.faction,
            "intra_position": s.intra_position, "intra_destination": s.intra_destination,
            "intra_progress": s.intra_progress, "intra_speed": s.intra_speed,
            "risk_tolerance": s.risk_tolerance,
            "assigned_system": s.assigned_system, "assigned_station": s.assigned_station,
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

    # Load systems (only mutable state: inventories and prices)
    row = conn.execute("SELECT value FROM state WHERE key = ?", ("systems",)).fetchone()
    if row:
        systems_data = json.loads(row[0])
        for sid, data in systems_data.items():
            if sid not in sim.universe:
                continue
            for i, st_data in enumerate(data["stations"]):
                if i < len(sim.universe[sid].stations):
                    sim.universe[sid].stations[i].inventory = st_data.get("inventory", {})
                    sim.universe[sid].stations[i].price_cache = st_data.get("price_cache", {})

    # Load ships
    row = conn.execute("SELECT value FROM state WHERE key = ?", ("ships",)).fetchone()
    if row:
        ships_data = json.loads(row[0])
        sim.ships.clear()
        for sd in ships_data:
            sim.ships.append(NPCShip(
                id=sd["id"], name=sd["name"], cargo=sd.get("cargo", {}),
                cargo_capacity=sd.get("cargo_capacity", 200), fuel=sd.get("fuel", 100),
                location=sd["location"], destination=sd.get("destination", ""),
                progress=sd.get("progress", 0), speed=sd.get("speed", 1.0),
                state=sd.get("state", "idle"), state_timer=sd.get("state_timer", 0),
                role=sd.get("role", "trader"), ship_class=sd.get("ship_class", ""),
                route_path=sd.get("route_path", []),
                faction=sd.get("faction", ""),
                intra_position=sd.get("intra_position", ""),
                intra_destination=sd.get("intra_destination", ""),
                intra_progress=sd.get("intra_progress", 0.0),
                intra_speed=sd.get("intra_speed", 0.2),
                risk_tolerance=sd.get("risk_tolerance", 0.5),
                assigned_system=sd.get("assigned_system", ""),
                assigned_station=sd.get("assigned_station", ""),
            ))

    conn.close()
    return True


def clear_db():
    """Wipe the database (used by nuke)."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
