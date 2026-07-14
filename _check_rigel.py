import sqlite3, math
conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row

# Get all Rigel system objects
cur = conn.cursor()
cur.execute("SELECT * FROM system_objects WHERE system_id='rigel' ORDER BY obj_type, distance")
objects = cur.fetchall()

print(f"Rigel system: {len(objects)} objects\n")

# Compute SS coords the same way local_space.py does
obj_ss = {}
# First pass: no parent
for obj in objects:
    if obj['parent']:
        continue
    ss_x = obj['distance'] * math.cos(obj['angle'])
    ss_z = obj['distance'] * math.sin(obj['angle'])
    incl = obj['inclination'] or 0
    ss_y = obj['distance'] * math.sin(incl)
    obj_ss[obj['id']] = (ss_x, ss_y, ss_z)

# Second pass: with parent
for obj in objects:
    if obj['parent']:
        parent_ss = obj_ss.get(obj['parent'], (0, 0, 0))
        ss_x = parent_ss[0] + obj['distance'] * math.cos(obj['angle'])
        ss_z = parent_ss[2] + obj['distance'] * math.sin(obj['angle'])
        incl = obj['inclination'] or 0
        ss_y = parent_ss[1] + obj['distance'] * math.sin(incl)
        obj_ss[obj['id']] = (ss_x, ss_y, ss_z)

# Print all objects with their SS coords
for obj in objects:
    ss = obj_ss.get(obj['id'], (0,0,0))
    parent_info = ''
    if obj['parent']:
        p = conn.execute("SELECT name FROM system_objects WHERE id=?", (obj['parent'],)).fetchone()
        parent_info = f" [parent: {p['name'] if p else obj['parent']}]"
    print(f"  {obj['obj_type']:8s} {obj['name'][:40]:40s} dist={obj['distance']:8.4f} SS=({ss[0]:8.4f}, {ss[1]:8.4f}, {ss[2]:8.4f}){parent_info}")

# Check for objects at or near 0,0,0
print("\n\nObjects near SS origin (dist < 0.01 AU):")
for obj in objects:
    ss = obj_ss.get(obj['id'], (0,0,0))
    d = math.sqrt(ss[0]**2 + ss[1]**2 + ss[2]**2)
    if d < 0.01 and obj['obj_type'] != 'star':
        print(f"  {obj['obj_type']} {obj['name']} SS=({ss[0]:.6f}, {ss[1]:.6f}, {ss[2]:.6f}) dist_from_star={d:.6f} AU")

# Check for duplicate/stacked stations
print("\n\nStations and their positions:")
stations = [o for o in objects if o['obj_type'] == 'station']
for s in stations:
    ss = obj_ss.get(s['id'], (0,0,0))
    print(f"  {s['name'][:45]:45s} dist={s['distance']:.4f} parent={s['parent'] or 'none':12s} SS=({ss[0]:.4f}, {ss[1]:.4f}, {ss[2]:.4f})")
