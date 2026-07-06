import sqlite3, traceback
conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT * FROM system_objects WHERE system_id='rigel' LIMIT 3").fetchall()
for r in rows:
    cols = r.keys()
    print(f"  {r['name']}: cols={cols}")
    print(f"    planet_type={r['planet_type'] if 'planet_type' in cols else 'NO COL'}")
    print(f"    radius_km={r['radius_km'] if 'radius_km' in cols else 'NO COL'}")
    break
conn.close()
