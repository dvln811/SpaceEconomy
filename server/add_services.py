"""Add services column to stations and populate based on station type."""
import sqlite3, json, os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

SERVICES = {
    'mining_colony': ['market', 'refuel', 'storage'],
    'refinery': ['market', 'refuel', 'storage', 'repair'],
    'factory': ['market', 'storage', 'repair'],
    'component_works': ['market', 'storage', 'fitting'],
    'shipyard': ['market', 'repair', 'refuel', 'fitting', 'storage'],
    'trade_hub': ['market', 'repair', 'refuel', 'agents', 'fitting', 'storage'],
    'military_base': ['market', 'repair', 'refuel', 'agents', 'storage'],
}

conn = sqlite3.connect(DB)
cols = [r[1] for r in conn.execute('PRAGMA table_info(stations)')]
if 'services' not in cols:
    conn.execute("ALTER TABLE stations ADD COLUMN services TEXT DEFAULT '[]'")
    print("Added services column")

rows = conn.execute("SELECT id, station_type FROM stations").fetchall()
for r in rows:
    svcs = json.dumps(SERVICES.get(r[1], ['market']))
    conn.execute("UPDATE stations SET services=? WHERE id=?", (svcs, r[0]))

conn.commit()
print(f"Updated services for {len(rows)} stations")
conn.close()
