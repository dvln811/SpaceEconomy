import sqlite3
conn = sqlite3.connect('data/game_data.db')
# Find Rigel II-a
cur = conn.cursor()
cur.execute("SELECT id, name, inclination FROM system_objects WHERE system_id='rigel' AND name='Rigel II-a'")
r = cur.fetchone()
print(f"Before: {r[1]} inclination={r[2]}")
conn.execute("UPDATE system_objects SET inclination=0.04 WHERE id=?", (r[0],))
conn.commit()
cur.execute("SELECT id, name, inclination FROM system_objects WHERE id=?", (r[0],))
r = cur.fetchone()
print(f"After: {r[1]} inclination={r[2]}")
