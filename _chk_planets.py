import sqlite3, math
conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row
objs = conn.execute("SELECT name, obj_type, distance, angle, radius_km FROM system_objects WHERE system_id='rigel' AND obj_type='planet' LIMIT 3").fetchall()
for o in objs:
    ss_x = o['distance'] * math.cos(o['angle'])
    ss_z = o['distance'] * math.sin(o['angle'])
    print(f"{o['name']:20s} dist={o['distance']:.2f}AU  ss=({ss_x:.4f}, {ss_z:.4f})  radius={o['radius_km']:.0f}km")
