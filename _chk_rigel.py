import sqlite3, math
conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row

print("=== RIGEL SYSTEM ===\n")

objs = conn.execute("SELECT id, name, obj_type, distance, angle, parent, radius_km, planet_type, station_id FROM system_objects WHERE system_id='rigel' ORDER BY obj_type, distance").fetchall()

for o in objs:
    ss_x = o['distance'] * math.cos(o['angle'])
    ss_z = o['distance'] * math.sin(o['angle'])
    parent = f"  parent={o['parent']}" if o['parent'] else ""
    station = f"  station_id={o['station_id']}" if o['station_id'] else ""
    radius = f"  r={o['radius_km']:.0f}km" if o['radius_km'] else ""
    ptype = f"  type={o['planet_type']}" if o['planet_type'] else ""
    print(f"  {o['obj_type']:8s} {o['name']:25s} dist={o['distance']:6.3f}AU  ss=({ss_x:7.4f},{ss_z:7.4f}){radius}{ptype}{parent}{station}")

print("\n=== STATIONS ===")
stations = conn.execute("SELECT id, name, station_type FROM stations WHERE system_id='rigel'").fetchall()
for s in stations:
    print(f"  {s['name']:30s} type={s['station_type']}")
