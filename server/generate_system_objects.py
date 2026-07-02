"""Generate system objects (stars, planets, moons, gates, asteroid belts) for all systems."""
import sqlite3
import math
import random
import os

random.seed(42)

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

STAR_TYPES = ['G-type', 'K-type', 'M-type', 'A-type', 'F-type', 'B-type', 'Red Giant', 'White Dwarf', 'Binary']
PLANET_NAMES = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']


def generate():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Clear existing
    conn.execute("DELETE FROM system_objects")

    systems = conn.execute("SELECT id, name, system_type, security FROM systems").fetchall()
    connections = {}
    for r in conn.execute("SELECT from_id, to_id FROM system_connections"):
        connections.setdefault(r['from_id'], []).append(r['to_id'])

    # Get asteroid fields per system
    fields = {}
    for r in conn.execute("SELECT id, system_id, name FROM asteroid_fields"):
        fields.setdefault(r['system_id'], []).append(r)

    obj_count = 0
    for sys in systems:
        sid = sys['id']
        sname = sys['name']
        objects = []

        # Star (center)
        star_type = random.choice(STAR_TYPES)
        obj_count += 1
        objects.append((f"obj_{obj_count:06d}", f"{sname} Star", sid, 'star', 0, 0, '', ''))

        # Planets (2-5)
        num_planets = random.randint(2, 5)
        planet_ids = []
        for pi in range(num_planets):
            obj_count += 1
            pid = f"obj_{obj_count:06d}"
            pname = f"{sname} {PLANET_NAMES[pi]}"
            dist = 2.0 + pi * 1.5 + random.uniform(0, 1.0)
            angle = random.uniform(0, 2 * math.pi)
            objects.append((pid, pname, sid, 'planet', round(dist, 2), round(angle, 4), '', ''))
            planet_ids.append((pid, dist, angle))

            # Moons (0-2 per planet)
            num_moons = random.randint(0, 2) if pi < 4 else 0
            for mi in range(num_moons):
                obj_count += 1
                mid = f"obj_{obj_count:06d}"
                mname = f"{pname}-{'abc'[mi]}"
                mdist = dist + 0.3 + mi * 0.2
                mangle = angle + random.uniform(-0.3, 0.3)
                objects.append((mid, mname, sid, 'moon', round(mdist, 2), round(mangle, 4), pid, ''))

        # Stations (placed at mid-range distances)
        stations = conn.execute("SELECT id, name FROM stations WHERE system_id=?", (sid,)).fetchall()
        for si, st in enumerate(stations):
            obj_count += 1
            dist = 3.0 + si * 2.0 + random.uniform(0, 1.0)
            angle = random.uniform(0, 2 * math.pi)
            objects.append((f"obj_{obj_count:06d}", st['name'], sid, 'station', round(dist, 2), round(angle, 4), '', '', st['id']))

        # Asteroid belts
        sys_fields = fields.get(sid, [])
        for fi, f in enumerate(sys_fields):
            obj_count += 1
            dist = 5.0 + fi * 1.5 + random.uniform(0, 1.5)
            angle = random.uniform(0, 2 * math.pi)
            # Store field_id in connects_to for asteroid model lookup
            objects.append((f"obj_{obj_count:06d}", f['name'], sid, 'belt', round(dist, 2), round(angle, 4), '', f['id']))

        # Jump gates (one per connection, outer ring)
        sys_conns = connections.get(sid, [])
        for ci, target_id in enumerate(sys_conns):
            obj_count += 1
            dist = 10.0 + random.uniform(0, 3.0)
            angle = (2 * math.pi * ci / max(len(sys_conns), 1)) + random.uniform(-0.2, 0.2)
            target_name = conn.execute("SELECT name FROM systems WHERE id=?", (target_id,)).fetchone()
            gate_name = f"Gate to {target_name['name']}" if target_name else f"Gate to {target_id}"
            objects.append((f"obj_{obj_count:06d}", gate_name, sid, 'gate', round(dist, 2), round(angle, 4), '', target_id))

        # Write all objects
        for obj in objects:
            if len(obj) == 9:
                conn.execute("INSERT INTO system_objects (id, name, system_id, obj_type, distance, angle, parent, connects_to, station_id) VALUES (?,?,?,?,?,?,?,?,?)", obj)
            else:
                conn.execute("INSERT INTO system_objects (id, name, system_id, obj_type, distance, angle, parent, connects_to) VALUES (?,?,?,?,?,?,?,?)", obj)

    conn.commit()
    conn.close()
    print(f"Generated {obj_count} system objects across {len(systems)} systems")


if __name__ == '__main__':
    generate()
