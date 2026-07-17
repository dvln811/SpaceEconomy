import sqlite3
conn = sqlite3.connect('data/game_data.db')
for r in conn.execute("SELECT id, name, obj_type, connects_to FROM system_objects WHERE system_id='rigel' AND obj_type IN ('gate','station')").fetchall():
    print(r)
