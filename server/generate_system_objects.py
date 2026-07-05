"""Generate system objects (stars, planets, moons, gates, asteroid belts) for all systems.
Assigns planet/moon types, radii, stats, resources, and rings."""
import sqlite3
import math
import random
import json
import os

random.seed(42)

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

STAR_TYPES = ['G-type', 'K-type', 'M-type', 'A-type', 'F-type', 'B-type', 'Red Giant', 'White Dwarf', 'Binary']
PLANET_NAMES = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']

# ── Planet Type Definitions ──
PLANET_TYPES = {
    'rocky': {
        'radius_range': (2000, 5000),
        'temp_range': (-200, 400),
        'atmosphere': ['None', 'Thin CO2', 'Thin Nitrogen'],
        'gravity_range': (0.2, 0.6),
        'resources': ['Iron', 'Nickel', 'Lithium', 'Rare Earths', 'Titanium'],
        'ring_chance': 0.05,
        'color_base': 0x8b6b3a,
    },
    'terrestrial': {
        'radius_range': (5000, 8000),
        'temp_range': (-50, 50),
        'atmosphere': ['Breathable N2/O2', 'Dense N2/O2', 'Thin O2'],
        'gravity_range': (0.8, 1.2),
        'resources': ['Organics', 'Water', 'Biomass', 'Timber', 'Agricultural'],
        'ring_chance': 0.0,
        'color_base': 0x1a5c3a,
    },
    'desert': {
        'radius_range': (4000, 7000),
        'temp_range': (50, 300),
        'atmosphere': ['Thin CO2', 'Toxic SO2', 'None'],
        'gravity_range': (0.5, 1.0),
        'resources': ['Silicon', 'Titanium', 'Glass', 'Ceramic Compounds', 'Quartz'],
        'ring_chance': 0.0,
        'color_base': 0xc4956a,
    },
    'ocean': {
        'radius_range': (5000, 9000),
        'temp_range': (0, 40),
        'atmosphere': ['Breathable Humid', 'Dense Humid', 'Tropical'],
        'gravity_range': (0.9, 1.3),
        'resources': ['Water', 'Deuterium', 'Coral', 'Aquatic Biomass', 'Salt'],
        'ring_chance': 0.0,
        'color_base': 0x2a4a6b,
    },
    'ice': {
        'radius_range': (3000, 6000),
        'temp_range': (-250, -50),
        'atmosphere': ['Thin Nitrogen', 'None', 'Thin Methane'],
        'gravity_range': (0.3, 0.7),
        'resources': ['Cryo Compounds', 'Helium-3', 'Frozen Methane', 'Ice Water'],
        'ring_chance': 0.15,
        'color_base': 0x6b8baa,
    },
    'gas_giant': {
        'radius_range': (30000, 70000),
        'temp_range': (-200, -100),
        'atmosphere': ['Crushing H2/He', 'Superdense H2', 'Metallic Hydrogen'],
        'gravity_range': (2.0, 5.0),
        'resources': ['Hydrogen', 'Helium-3', 'Exotic Gas', 'Plasma Compounds'],
        'ring_chance': 0.6,
        'color_base': 0xc49060,
    },
    'ice_giant': {
        'radius_range': (15000, 30000),
        'temp_range': (-220, -150),
        'atmosphere': ['Dense Methane/Ammonia', 'H2/He with Ice Clouds'],
        'gravity_range': (1.2, 2.5),
        'resources': ['Methane', 'Ammonia', 'Deuterium', 'Frozen Compounds'],
        'ring_chance': 0.4,
        'color_base': 0x4a7a8a,
    },
    'volcanic': {
        'radius_range': (3000, 6000),
        'temp_range': (200, 800),
        'atmosphere': ['Toxic SO2/CO2', 'Dense Sulfuric', 'Volcanic Ash'],
        'gravity_range': (0.4, 0.9),
        'resources': ['Sulfur', 'Heavy Metals', 'Obsidian', 'Magma Crystals', 'Platinum'],
        'ring_chance': 0.08,
        'color_base': 0x8b3a1a,
    },
    'super_earth': {
        'radius_range': (8000, 15000),
        'temp_range': (-100, 200),
        'atmosphere': ['Dense N2/CO2', 'Superdense O2', 'Thick Argon'],
        'gravity_range': (1.5, 3.0),
        'resources': ['Compressed Carbon', 'High-G Minerals', 'Diamond', 'Dense Alloys'],
        'ring_chance': 0.1,
        'color_base': 0x4a6a4a,
    },
}

# Weight distribution for planet types based on orbital distance
# Inner system (< 4 AU): rocky, desert, volcanic, terrestrial
# Mid system (4-8 AU): terrestrial, ocean, super_earth, ice
# Outer system (> 8 AU): gas_giant, ice_giant, ice
INNER_TYPES = ['rocky', 'rocky', 'desert', 'volcanic', 'terrestrial']
MID_TYPES = ['terrestrial', 'ocean', 'super_earth', 'ice', 'desert']
OUTER_TYPES = ['gas_giant', 'gas_giant', 'ice_giant', 'ice_giant', 'ice']

# ── Moon Type Definitions ──
MOON_TYPES = {
    'rocky_moon': {
        'radius_range': (200, 1500),
        'temp_range': (-200, 100),
        'atmosphere': ['None', 'Trace'],
        'gravity_range': (0.05, 0.3),
        'resources': ['Iron', 'Nickel', 'Regolith', 'Rare Earths'],
        'color_base': 0x6a6a6a,
    },
    'ice_moon': {
        'radius_range': (300, 2000),
        'temp_range': (-250, -100),
        'atmosphere': ['None', 'Thin O2'],
        'gravity_range': (0.05, 0.2),
        'resources': ['Ice Water', 'Subsurface Ocean', 'Cryo Compounds', 'Helium-3'],
        'color_base': 0x8aa8c0,
    },
    'volcanic_moon': {
        'radius_range': (200, 800),
        'temp_range': (100, 600),
        'atmosphere': ['Thin SO2', 'Trace Volcanic'],
        'gravity_range': (0.05, 0.15),
        'resources': ['Sulfur', 'Exotic Minerals', 'Magma Crystals', 'Heavy Metals'],
        'color_base': 0x8b5a2a,
    },
}

RING_TYPES = ['rocky', 'icy', 'dusty']


def pick_planet_type(orbital_dist):
    """Pick a planet type based on orbital distance from star."""
    if orbital_dist < 4.0:
        return random.choice(INNER_TYPES)
    elif orbital_dist < 8.0:
        return random.choice(MID_TYPES)
    else:
        return random.choice(OUTER_TYPES)


def pick_moon_type(parent_type):
    """Pick a moon type based on parent planet."""
    if parent_type in ('gas_giant', 'ice_giant'):
        return random.choice(['ice_moon', 'ice_moon', 'rocky_moon', 'volcanic_moon'])
    elif parent_type == 'volcanic':
        return random.choice(['volcanic_moon', 'rocky_moon'])
    else:
        return random.choice(['rocky_moon', 'rocky_moon', 'ice_moon'])


def generate_stats(body_type, type_def):
    """Generate full stats for a planet/moon."""
    radius = random.randint(*type_def['radius_range'])
    temp = random.randint(*type_def['temp_range'])
    gravity = round(random.uniform(*type_def['gravity_range']), 2)
    atmosphere = random.choice(type_def['atmosphere'])
    # Pick 2-4 resources with richness levels
    num_resources = random.randint(2, min(4, len(type_def['resources'])))
    resources = []
    for res in random.sample(type_def['resources'], num_resources):
        richness = random.choice(['Trace', 'Low', 'Moderate', 'High', 'Rich'])
        resources.append({'name': res, 'richness': richness})
    # Rings
    has_rings = random.random() < type_def.get('ring_chance', 0)
    ring_type = random.choice(RING_TYPES) if has_rings else None
    # Orbital/rotation periods
    orbital_period = round(random.uniform(10, 800), 1)  # days
    rotation_period = round(random.uniform(4, 200), 1)  # hours
    # Magnetic field
    mag_field = round(random.uniform(0, gravity * 2), 2)  # correlates with mass

    return {
        'radius_km': radius,
        'temperature': temp,
        'gravity': gravity,
        'atmosphere': atmosphere,
        'resources': resources,
        'has_rings': has_rings,
        'ring_type': ring_type,
        'orbital_period_days': orbital_period,
        'rotation_hours': rotation_period,
        'magnetic_field': mag_field,
    }


def generate():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Ensure columns exist (add if missing for existing DBs)
    try:
        conn.execute("ALTER TABLE system_objects ADD COLUMN planet_type TEXT DEFAULT ''")
    except: pass
    try:
        conn.execute("ALTER TABLE system_objects ADD COLUMN radius_km REAL DEFAULT 0")
    except: pass
    try:
        conn.execute("ALTER TABLE system_objects ADD COLUMN stats TEXT DEFAULT ''")
    except: pass

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

        # Star (center)
        star_type = random.choice(STAR_TYPES)
        obj_count += 1
        conn.execute("INSERT INTO system_objects (id, name, system_id, obj_type, distance, angle, parent, connects_to) VALUES (?,?,?,?,?,?,?,?)",
                     (f"obj_{obj_count:06d}", f"{sname} Star", sid, 'star', 0, 0, '', ''))

        # Planets (2-5)
        num_planets = random.randint(2, 5)
        planet_data = []  # (id, dist, angle, planet_type)
        for pi in range(num_planets):
            obj_count += 1
            pid = f"obj_{obj_count:06d}"
            pname = f"{sname} {PLANET_NAMES[pi]}"
            dist = 2.0 + pi * 1.5 + random.uniform(0, 1.0)
            angle = random.uniform(0, 2 * math.pi)

            # Assign planet type based on orbital distance
            ptype = pick_planet_type(dist)
            type_def = PLANET_TYPES[ptype]
            stats = generate_stats(ptype, type_def)

            conn.execute(
                "INSERT INTO system_objects (id, name, system_id, obj_type, distance, angle, parent, connects_to, planet_type, radius_km, stats) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (pid, pname, sid, 'planet', round(dist, 2), round(angle, 4), '', '', ptype, stats['radius_km'], json.dumps(stats))
            )
            planet_data.append((pid, dist, angle, ptype))

            # Moons (0-3 for gas giants, 0-2 for others)
            max_moons = 3 if ptype in ('gas_giant', 'ice_giant') else 2
            num_moons = random.randint(0, max_moons) if pi < 6 else 0
            for mi in range(num_moons):
                obj_count += 1
                mid = f"obj_{obj_count:06d}"
                mname = f"{pname}-{'abcde'[mi]}"
                # Moon distance relative to parent
                mdist = 0.003 + mi * 0.002 + random.uniform(0, 0.001)
                mangle = random.uniform(0, 2 * math.pi)

                mtype = pick_moon_type(ptype)
                mtype_def = MOON_TYPES[mtype]
                mstats = generate_stats(mtype, mtype_def)

                conn.execute(
                    "INSERT INTO system_objects (id, name, system_id, obj_type, distance, angle, parent, connects_to, planet_type, radius_km, stats) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (mid, mname, sid, 'moon', round(mdist, 4), round(mangle, 4), pid, '', mtype, mstats['radius_km'], json.dumps(mstats))
                )

        # Stations (placed at mid-range distances)
        stations = conn.execute("SELECT id, name FROM stations WHERE system_id=?", (sid,)).fetchall()
        for si, st in enumerate(stations):
            obj_count += 1
            dist = 3.0 + si * 2.0 + random.uniform(0, 1.0)
            angle = random.uniform(0, 2 * math.pi)
            conn.execute(
                "INSERT INTO system_objects (id, name, system_id, obj_type, distance, angle, parent, connects_to, station_id) VALUES (?,?,?,?,?,?,?,?,?)",
                (f"obj_{obj_count:06d}", st['name'], sid, 'station', round(dist, 2), round(angle, 4), '', '', st['id'])
            )

        # Asteroid belts
        sys_fields = fields.get(sid, [])
        for fi, f in enumerate(sys_fields):
            obj_count += 1
            dist = 5.0 + fi * 1.5 + random.uniform(0, 1.5)
            angle = random.uniform(0, 2 * math.pi)
            conn.execute(
                "INSERT INTO system_objects (id, name, system_id, obj_type, distance, angle, parent, connects_to) VALUES (?,?,?,?,?,?,?,?)",
                (f"obj_{obj_count:06d}", f['name'], sid, 'belt', round(dist, 2), round(angle, 4), '', f['id'])
            )

        # Jump gates (one per connection, outer ring)
        sys_conns = connections.get(sid, [])
        for ci, target_id in enumerate(sys_conns):
            obj_count += 1
            dist = 10.0 + random.uniform(0, 3.0)
            angle = (2 * math.pi * ci / max(len(sys_conns), 1)) + random.uniform(-0.2, 0.2)
            target_name = conn.execute("SELECT name FROM systems WHERE id=?", (target_id,)).fetchone()
            gate_name = f"Gate to {target_name['name']}" if target_name else f"Gate to {target_id}"
            conn.execute(
                "INSERT INTO system_objects (id, name, system_id, obj_type, distance, angle, parent, connects_to) VALUES (?,?,?,?,?,?,?,?)",
                (f"obj_{obj_count:06d}", gate_name, sid, 'gate', round(dist, 2), round(angle, 4), '', target_id)
            )

    conn.commit()
    conn.close()
    print(f"Generated {obj_count} system objects across {len(systems)} systems")


if __name__ == '__main__':
    generate()
