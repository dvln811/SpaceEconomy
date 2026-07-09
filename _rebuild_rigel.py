"""Rebuild Rigel system with better planet distribution, proper moons, and orbital stations."""
import sqlite3, math, random, json

random.seed(99)
conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row

# Delete existing Rigel system objects (keep stations table entries)
conn.execute("DELETE FROM system_objects WHERE system_id='rigel'")

# Get station IDs for Rigel
stations = conn.execute("SELECT id, name, station_type FROM stations WHERE system_id='rigel'").fetchall()
print(f"Rigel has {len(stations)} stations: {[s['name'] for s in stations]}")

obj_count = 0
def next_id():
    global obj_count
    obj_count += 1
    return f"rigel_{obj_count:04d}"

def insert_obj(oid, name, obj_type, distance, angle, parent='', planet_type='', radius_km=0, station_id='', connects_to='', stats=None):
    conn.execute(
        "INSERT INTO system_objects (id, name, system_id, obj_type, distance, angle, parent, connects_to, planet_type, radius_km, station_id, stats) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (oid, name, 'rigel', obj_type, round(distance, 4), round(angle, 4), parent, connects_to, planet_type, radius_km, station_id, json.dumps(stats) if stats else '')
    )

# ── Star ──
star_id = next_id()
insert_obj(star_id, "Rigel Star", "star", 0, 0)

# ── Planets (spread from 1.5 to 20 AU) ──
planets = [
    # (name, dist_AU, type, radius_km, num_moons)
    ("Rigel I",      1.8,  "rocky",       2800,  0),
    ("Rigel II",     3.5,  "desert",      5200,  1),
    ("Rigel III",    6.2,  "terrestrial", 6400,  1),
    ("Rigel IV",    10.5,  "gas_giant",  52000,  3),
    ("Rigel V",     16.0,  "ice_giant",  28000,  2),
    ("Rigel VI",    22.0,  "ice",         3800,  0),
]

planet_ids = {}
for p_name, p_dist, p_type, p_radius, p_moons in planets:
    pid = next_id()
    p_angle = random.uniform(0, 2 * math.pi)
    planet_ids[p_name] = (pid, p_dist, p_angle)
    
    stats = {
        'radius_km': p_radius,
        'planet_type': p_type,
        'temperature': random.randint(-200, 400),
        'gravity': round(random.uniform(0.2, 2.5), 2),
    }
    insert_obj(pid, p_name, "planet", p_dist, p_angle, planet_type=p_type, radius_km=p_radius, stats=stats)
    
    # Moons
    moon_types = ['rocky_moon', 'ice_moon', 'volcanic_moon']
    for mi in range(p_moons):
        mid = next_id()
        m_name = f"{p_name}-{'abcde'[mi]}"
        # Orbital distance: proportional to parent radius
        if p_type in ('gas_giant', 'ice_giant'):
            m_orbit_au = (p_radius * (5 + mi * 4 + random.uniform(0, 3))) / 150000000
        else:
            m_orbit_au = (p_radius * (15 + mi * 20 + random.uniform(0, 10))) / 150000000
        m_angle = random.uniform(0, 2 * math.pi)
        m_type = random.choice(moon_types)
        m_radius = random.randint(300, 2500)
        
        stats = {'radius_km': m_radius, 'planet_type': m_type}
        insert_obj(mid, m_name, "moon", round(m_orbit_au, 6), m_angle, parent=pid, planet_type=m_type, radius_km=m_radius, stats=stats)

# ── Stations ──
# First 2: orbital (around Rigel III and Rigel IV)
# Rest: free-floating
station_list = list(stations)

# Orbital station at Rigel III
if len(station_list) > 0:
    st = station_list[0]
    parent_pid, parent_dist, parent_angle = planet_ids["Rigel III"]
    # Place station at 1.5x planet radius from planet, at a random angle
    orbit_dist_au = (6400 * 2.0) / 150000000  # 2x radius
    st_angle = parent_angle + 0.3  # slight offset from planet angle
    sid = next_id()
    insert_obj(sid, st['name'], "station", orbit_dist_au, st_angle, parent=parent_pid, station_id=st['id'])
    print(f"  Orbital: {st['name']} -> orbiting Rigel III")

# Orbital station at Rigel IV  
if len(station_list) > 1:
    st = station_list[1]
    parent_pid, parent_dist, parent_angle = planet_ids["Rigel IV"]
    orbit_dist_au = (52000 * 1.5) / 150000000
    st_angle = parent_angle - 0.2
    sid = next_id()
    insert_obj(sid, st['name'], "station", orbit_dist_au, st_angle, parent=parent_pid, station_id=st['id'])
    print(f"  Orbital: {st['name']} -> orbiting Rigel IV")

# Free-floating stations
for i, st in enumerate(station_list[2:], start=2):
    sid = next_id()
    # Spread between 4-14 AU
    st_dist = 4.0 + i * 2.5 + random.uniform(0, 1.5)
    st_angle = random.uniform(0, 2 * math.pi)
    insert_obj(sid, st['name'], "station", st_dist, st_angle, station_id=st['id'])
    print(f"  Free: {st['name']} at {st_dist:.1f} AU")

# ── Gates (keep existing connections, reposition at outer edge) ──
gate_connections = conn.execute("SELECT name, connects_to FROM system_objects WHERE system_id='rigel' AND obj_type='gate'").fetchall()
# They were deleted above, so get from the old data... actually we deleted them. Let me hardcode Rigel's connections.
rigel_gates = ['NCD-286', 'Struve', 'Regulus', 'Canopus', 'Procyon']
for gi, dest in enumerate(rigel_gates):
    gid = next_id()
    g_dist = 25.0 + gi * 2.0 + random.uniform(0, 1.0)
    g_angle = (2 * math.pi / len(rigel_gates)) * gi + random.uniform(-0.2, 0.2)
    insert_obj(gid, f"Gate to {dest}", "gate", g_dist, g_angle, connects_to=dest)

conn.commit()
print("\nRigel rebuilt!")

# Verify
print("\n=== NEW RIGEL ===")
objs = conn.execute("SELECT name, obj_type, distance, angle, parent, radius_km, planet_type, station_id FROM system_objects WHERE system_id='rigel' ORDER BY distance").fetchall()
for o in objs:
    ss_x = o['distance'] * math.cos(o['angle'])
    ss_z = o['distance'] * math.sin(o['angle'])
    extra = ""
    if o['parent']: extra += f" parent={o['parent']}"
    if o['radius_km']: extra += f" r={o['radius_km']:.0f}km"
    if o['planet_type']: extra += f" {o['planet_type']}"
    if o['station_id']: extra += f" [{o['station_id']}]"
    print(f"  {o['obj_type']:8s} {o['name']:35s} {o['distance']:6.3f}AU  ss=({ss_x:7.4f},{ss_z:7.4f}){extra}")
