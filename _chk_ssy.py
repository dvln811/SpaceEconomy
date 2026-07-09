import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

from server.local_space import SystemObject
import sqlite3, math

conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row
objs = conn.execute("SELECT id, name, obj_type, distance, angle, parent, radius_km, planet_type FROM system_objects WHERE system_id='rigel' ORDER BY distance").fetchall()

# Replicate the ss_y calculation from local_space.py
obj_ss = {}
for obj in objs:
    if obj['obj_type'] == 'moon' and obj['parent']:
        continue
    ss_x = obj['distance'] * math.cos(obj['angle'])
    ss_z = obj['distance'] * math.sin(obj['angle'])
    inclination = (hash(obj['id']) % 200 - 100) / 1000.0
    ss_y = obj['distance'] * math.sin(inclination)
    obj_ss[obj['id']] = (ss_x, ss_y, ss_z)

for obj in objs:
    if obj['obj_type'] == 'moon' and obj['parent']:
        parent_ss = obj_ss.get(obj['parent'], (0, 0, 0))
        ss_x = parent_ss[0] + obj['distance'] * math.cos(obj['angle'])
        ss_y = parent_ss[1] + obj['distance'] * math.sin((hash(obj['id']) % 200 - 100) / 500.0)
        ss_z = parent_ss[2] + obj['distance'] * math.sin(obj['angle'])
        obj_ss[obj['id']] = (ss_x, ss_y, ss_z)

for obj in objs:
    ss = obj_ss.get(obj['id'], (0,0,0))
    if obj['distance'] > 0.01:
        print(f"  {obj['obj_type']:8s} {obj['name']:35s} dist={obj['distance']:6.2f}AU  ss_y={ss[1]:+.4f}AU  incl_deg={math.degrees(math.asin(ss[1]/(obj['distance'] or 1))):.1f}deg")
