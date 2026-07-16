import sqlite3
conn = sqlite3.connect('data/game_data.db')
r = conn.execute("SELECT name, inclination FROM system_objects WHERE name='Rigel II-a'").fetchone()
print(r)
