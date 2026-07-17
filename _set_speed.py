import sqlite3
conn = sqlite3.connect('data/game_data.db')
conn.execute("UPDATE ships SET speed=1000 WHERE id='pinto_runner'")
conn.commit()
print('Pinto Runner speed set to 1000 m/s')
