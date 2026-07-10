import sqlite3, json
conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row
r = conn.execute("SELECT name, geometry FROM ships WHERE name LIKE '%Pinto%' LIMIT 1").fetchone()
if r:
    print(f"Found: {r['name']}")
    print(r['geometry'])
else:
    print("Not found - trying all ships")
    for row in conn.execute("SELECT name FROM ships LIMIT 5").fetchall():
        print(f"  {row['name']}")
