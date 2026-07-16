import sqlite3, math
conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT * FROM system_objects WHERE system_id='rigel' AND (obj_type='planet' OR obj_type='moon') ORDER BY obj_type, name")
for r in cur.fetchall():
    print(f'{r["obj_type"]:6s} {r["name"]:20s} dist={r["distance"]:.6f} angle={r["angle"]:.4f} parent={r["parent"] or "":12s} radius={r["radius_km"]}km incl={r["inclination"]}')

# Compute SS coords
print("\nSS Coordinates:")
cur.execute("SELECT * FROM system_objects WHERE system_id='rigel' ORDER BY obj_type")
objects = cur.fetchall()
obj_ss = {}
for o in objects:
    if o['parent']:
        continue
    ss_x = o['distance'] * math.cos(o['angle'])
    ss_z = o['distance'] * math.sin(o['angle'])
    incl = o['inclination'] or 0
    ss_y = o['distance'] * math.sin(incl)
    obj_ss[o['id']] = (ss_x, ss_y, ss_z)
for o in objects:
    if o['parent']:
        pss = obj_ss.get(o['parent'], (0,0,0))
        ss_x = pss[0] + o['distance'] * math.cos(o['angle'])
        ss_z = pss[2] + o['distance'] * math.sin(o['angle'])
        incl = o['inclination'] or 0
        ss_y = pss[1] + o['distance'] * math.sin(incl)
        obj_ss[o['id']] = (ss_x, ss_y, ss_z)

for o in objects:
    if o['obj_type'] in ('planet', 'moon'):
        ss = obj_ss.get(o['id'], (0,0,0))
        # distance from parent
        if o['parent'] and o['parent'] in obj_ss:
            pss = obj_ss[o['parent']]
            d = math.sqrt((ss[0]-pss[0])**2 + (ss[1]-pss[1])**2 + (ss[2]-pss[2])**2) * 150000000
            print(f'  {o["name"]:20s} SS=({ss[0]:.6f},{ss[1]:.6f},{ss[2]:.6f}) dist_from_parent={d:.0f}km radius={o["radius_km"]}km')
        else:
            print(f'  {o["name"]:20s} SS=({ss[0]:.6f},{ss[1]:.6f},{ss[2]:.6f}) radius={o["radius_km"]}km')
