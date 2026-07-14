import sqlite3
conn = sqlite3.connect('data/game_data.db')
conn.execute("UPDATE player SET station_id='st_00028', docked=1, state='docked' WHERE id='player1'")
conn.commit()
print("Player reset to docked at st_00028 in Rigel")
