import sqlite3, os

conn = sqlite3.connect('data/game_data.db')
# Get Rigel I id
r = conn.execute("SELECT id FROM system_objects WHERE name='Rigel I' AND system_id='rigel'").fetchone()
rigel1_id = r[0]
print('Rigel I id:', rigel1_id)

# Undock player and set destination to Rigel I
conn.execute("UPDATE player SET docked=0, state='flight', station_id='', intra_destination=? WHERE id='player1'", (rigel1_id,))
conn.commit()
print('Player undocked, destination=Rigel I')
conn.close()
