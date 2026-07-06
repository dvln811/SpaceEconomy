"""Add one of each planet type to Rigel system for visual testing."""
import sqlite3, json, math, random
random.seed(99)

DB = 'data/game_data.db'
conn = sqlite3.connect(DB)

# Get current max obj_id
max_id = conn.execute("SELECT MAX(CAST(SUBSTR(id, 5) AS INTEGER)) FROM system_objects").fetchone()[0] or 0

# Planet types to add
TYPES = ['rocky', 'terrestrial', 'desert', 'ocean', 'ice', 'gas_giant', 'ice_giant', 'volcanic', 'super_earth']

# Type definitions for stats
TYPE_DEFS = {
    'rocky': {'radius_range': (2000, 5000), 'temp_range': (-200, 400), 'atmo': ['None', 'Thin CO2'], 'grav': (0.2, 0.6), 'res': ['Iron', 'Nickel', 'Lithium'], 'ring': 0.0},
    'terrestrial': {'radius_range': (5000, 8000), 'temp_range': (-50, 50), 'atmo': ['Breathable N2/O2'], 'grav': (0.8, 1.2), 'res': ['Organics', 'Water', 'Biomass'], 'ring': 0.0},
    'desert': {'radius_range': (4000, 7000), 'temp_range': (50, 300), 'atmo': ['Thin CO2', 'Toxic SO2'], 'grav': (0.5, 1.0), 'res': ['Silicon', 'Titanium', 'Glass'], 'ring': 0.0},
    'ocean': {'radius_range': (5000, 9000), 'temp_range': (0, 40), 'atmo': ['Breathable Humid'], 'grav': (0.9, 1.3), 'res': ['Water', 'Deuterium', 'Coral'], 'ring': 0.0},
    'ice': {'radius_range': (3000, 6000), 'temp_range': (-250, -50), 'atmo': ['Thin Nitrogen'], 'grav': (0.3, 0.7), 'res': ['Cryo Compounds', 'Helium-3'], 'ring': 0.15},
    'gas_giant': {'radius_range': (35000, 70000), 'temp_range': (-200, -100), 'atmo': ['Crushing H2/He'], 'grav': (2.0, 5.0), 'res': ['Hydrogen', 'Helium-3', 'Exotic Gas'], 'ring': 1.0},
    'ice_giant': {'radius_range': (15000, 30000), 'temp_range': (-220, -150), 'atmo': ['Dense Methane/Ammonia'], 'grav': (1.2, 2.5), 'res': ['Methane', 'Ammonia', 'Deuterium'], 'ring': 0.5},
    'volcanic': {'radius_range': (3000, 6000), 'temp_range': (200, 800), 'atmo': ['Toxic SO2/CO2'], 'grav': (0.4, 0.9), 'res': ['Sulfur', 'Heavy Metals', 'Obsidian'], 'ring': 0.0},
    'super_earth': {'radius_range': (8000, 15000), 'temp_range': (-100, 200), 'atmo': ['Dense N2/CO2'], 'grav': (1.5, 3.0), 'res': ['Compressed Carbon', 'Diamond'], 'ring': 0.1},
}

NAMES = ['III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI']

# First delete existing planets/moons in Rigel (keep stations, gates, belts, star)
conn.execute("DELETE FROM system_objects WHERE system_id='rigel' AND obj_type IN ('planet', 'moon')")

for i, ptype in enumerate(TYPES):
    max_id += 1
    pid = f"obj_{max_id:06d}"
    name = f"Rigel {NAMES[i]}"
    dist = 2.0 + i * 1.2 + random.uniform(0, 0.5)
    angle = random.uniform(0, 2 * math.pi)
    
    td = TYPE_DEFS[ptype]
    radius = random.randint(*td['radius_range'])
    temp = random.randint(*td['temp_range'])
    grav = round(random.uniform(*td['grav']), 2)
    atmo = random.choice(td['atmo'])
    resources = [{'name': r, 'richness': random.choice(['Low', 'Moderate', 'High', 'Rich'])} for r in td['res']]
    has_rings = random.random() < td['ring']
    
    stats = json.dumps({
        'radius_km': radius,
        'temperature': temp,
        'gravity': grav,
        'atmosphere': atmo,
        'resources': resources,
        'has_rings': has_rings,
        'ring_type': random.choice(['rocky', 'icy', 'dusty']) if has_rings else None,
        'orbital_period_days': round(random.uniform(50, 500), 1),
        'rotation_hours': round(random.uniform(8, 100), 1),
        'magnetic_field': round(random.uniform(0, grav * 2), 2),
    })
    
    conn.execute(
        "INSERT INTO system_objects (id, name, system_id, obj_type, distance, angle, parent, connects_to, planet_type, radius_km, stats) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (pid, name, 'rigel', 'planet', round(dist, 2), round(angle, 4), '', '', ptype, radius, stats)
    )
    print(f"  Added {name}: {ptype} R={radius}km rings={has_rings}")
    
    # Add a moon to gas giants and ice giants
    if ptype in ('gas_giant', 'ice_giant'):
        max_id += 1
        mid = f"obj_{max_id:06d}"
        mname = f"{name}-a"
        mdist = 0.004 + random.uniform(0, 0.002)
        mangle = random.uniform(0, 2 * math.pi)
        mradius = random.randint(300, 1500)
        mstats = json.dumps({
            'radius_km': mradius, 'temperature': -180, 'gravity': 0.1,
            'atmosphere': 'None', 'resources': [{'name': 'Ice Water', 'richness': 'Moderate'}],
            'has_rings': False, 'ring_type': None,
            'orbital_period_days': 5.0, 'rotation_hours': 40.0, 'magnetic_field': 0.01,
        })
        conn.execute(
            "INSERT INTO system_objects (id, name, system_id, obj_type, distance, angle, parent, connects_to, planet_type, radius_km, stats) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (mid, mname, 'rigel', 'moon', round(mdist, 4), round(mangle, 4), pid, '', 'ice_moon', mradius, mstats)
        )
        print(f"    Added moon {mname}: ice_moon R={mradius}km")

conn.commit()
conn.close()
print("\nDone! Rigel now has one of each planet type.")
