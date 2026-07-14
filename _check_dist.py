import sqlite3
conn = sqlite3.connect('data/game_data.db')
cur = conn.cursor()
cur.execute("SELECT name, distance, parent FROM system_objects WHERE system_id='rigel' AND obj_type='station' AND parent != ''")
for r in cur.fetchall():
    print(f"  {r[0]}: distance={r[1]:.10f} AU = {r[1]*150000000:.0f} km")
