import sqlite3
conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM system_objects WHERE obj_type='station' AND parent != ''")
print('Orbital stations:', cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM system_objects WHERE obj_type='belt' AND parent != ''")
print('Orbital belts:', cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM system_objects WHERE obj_type='station'")
print('Total stations:', cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM system_objects WHERE obj_type='belt'")
print('Total belts:', cur.fetchone()[0])

print('\nSample orbital stations:')
cur.execute("SELECT id, name, system_id, distance, parent FROM system_objects WHERE obj_type='station' AND parent != '' LIMIT 5")
for r in cur.fetchall():
    # Get parent info
    p = conn.execute("SELECT name, radius_km FROM system_objects WHERE id=?", (r['parent'],)).fetchone()
    dist_km = r['distance'] * 150000000
    print(f"  {r['name']} | parent: {p['name'] if p else '?'} (r={p['radius_km'] if p else '?'}km) | orbit: {dist_km:.0f} km")
