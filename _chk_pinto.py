import sqlite3
conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row
r = conn.execute("SELECT id, name, hull_class FROM ships WHERE name LIKE '%Pinto%'").fetchone()
if r:
    print(f"ID: {r['id']}, Name: {r['name']}, Class: {r['hull_class']}")
else:
    print("Not found")

# Check how ship_geometry generates it
from server.ship_geometry import get_ship_geometry
geo = get_ship_geometry('pinto_runner')
print(f"Components: {len(geo.get('components', []))}")
print(f"Bounds: {geo.get('bounds', {})}")
