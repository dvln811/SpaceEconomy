"""Generate a 2,500 system universe.

Layout:
- 6 faction homeworld clusters near center (named, high/med sec)
- Expanding outward: low-sec buffer zones
- Outer regions: null-sec with astronomical designations (ABC-123)
- ~175 named systems, ~2325 procedural
- 3D positions, Delaunay-like connectivity (avg 3-4 connections)
"""
import random
import math
import sqlite3
import json
import os
import string

random.seed(42)  # Reproducible

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

# === FACTION DEFINITIONS ===
FACTIONS = {
    'terran_fed': {'name': 'Terran Federation', 'pos': (0, 0, 0), 'systems': 40},
    'science_collective': {'name': 'Nexus Collective', 'pos': (300, 200, 50), 'systems': 30},
    'merchants_guild': {'name': 'Merchants Guild', 'pos': (-250, 250, -30), 'systems': 35},
    'free_states': {'name': 'Frontier Alliance', 'pos': (-300, -200, 40), 'systems': 30},
    'iron_compact': {'name': 'Iron Compact', 'pos': (200, -300, -50), 'systems': 25},
    'corsairs': {'name': 'The Corsairs', 'pos': (0, -400, 0), 'systems': 15},
}

# === NAMED STAR SYSTEMS (for faction cores) ===
CORE_NAMES = [
    # Terran Federation (~40)
    "Sol", "Terra Nova", "New Geneva", "Arcturus", "Vega", "Sirius", "Procyon", "Capella",
    "Deneb", "Altair", "Fomalhaut", "Polaris", "Rigel", "Aldebaran", "Antares", "Betelgeuse",
    "Canopus", "Achernar", "Regulus", "Spica", "Castor", "Pollux", "Mira", "Haven",
    "Meridian", "Cygnus", "Kepler", "Tau Ceti", "Epsilon Eridani", "Alpha Centauri",
    "Barnard's Star", "Ross 128", "Wolf 359", "Lalande", "Lacaille", "Groombridge",
    "Kruger", "Struve", "Gliese", "Proxima",
    # Nexus Collective (~30)
    "Nexus Prime", "Axiom", "Theorem", "Synthesis", "Paradigm", "Vector", "Quantum",
    "Helix", "Orbital", "Zenith", "Apogee", "Perihelion", "Eclipse", "Nebula",
    "Singularity", "Tesseract", "Parallax", "Quasar", "Pulsar", "Magnetar",
    "Prism", "Spectrum", "Photon", "Neutrino", "Hadron", "Boson", "Fermion",
    "Graviton", "Tachyon", "Chronos",
    # Merchants Guild (~35)
    "Grand Exchange", "Free Port", "Golden Gate", "Silk Road", "Bazaar",
    "Platinum Harbor", "Silver Bay", "Copper Landing", "Trade Wind", "Fair Haven",
    "Fortune", "Prosperity", "Dividend", "Margin Call", "Bull Market",
    "Gilt Edge", "Blue Chip", "Venture", "Enterprise", "Commerce",
    "Argent", "Sterling", "Aurelia", "Opulent", "Sovereign",
    "Treasury", "Mint", "Bullion", "Coinage", "Credit",
    "Ledger", "Mercantile", "Emporium", "Caravan", "Galleon",
    # Frontier Alliance (~30)
    "Liberty", "Defiance", "Independence", "Freehold", "Outpost",
    "Homestead", "Frontier", "Pioneer", "Trailhead", "Wildfire",
    "Dustbowl", "Rimward", "Deepsky", "Last Stop", "Far Reach",
    "Scatterpoint", "Driftwood", "Breakwater", "Iron Creek", "Rust Belt",
    "Salvage", "Wraith", "Grit", "Endurance", "Resolute",
    "Vagrant", "Nomad", "Wanderer", "Exile", "Waypoint",
    # Iron Compact (~25)
    "Crucible", "Anvil", "Hammer", "Forge", "Bastion",
    "Citadel", "Rampart", "Bulwark", "Garrison", "Arsenal",
    "Ironhold", "Steelgate", "Titanfall", "Dreadfort", "Warfront",
    "Siege", "Battlement", "Phalanx", "Legion", "Vanguard",
    "Colossus", "Juggernaut", "Warlord", "Conquest", "Dominion",
    # Corsairs (~15)
    "Skull Cove", "Black Wake", "Crimson Reach", "Shadow Port", "Venom",
    "Cutlass", "Marauder's Rest", "Plunder", "Rogue's End", "Blacktide",
    "Fang", "Dagger", "Scourge", "Blight", "Maelstrom",
]

# === SYSTEM TYPE DISTRIBUTION ===
SYSTEM_TYPES_CLAIMED = ['industrial', 'mining', 'trade', 'processing', 'shipyard', 'military', 'agricultural']
SYSTEM_TYPES_WILD = ['mining', 'frontier', 'industrial', 'processing']


def generate_null_sec_name():
    """Generate astronomical designation like JKT-482."""
    letters = ''.join(random.choices('ABCDEFGHJKLMNPQRSTVWXYZ', k=3))
    digits = f"{random.randint(100, 999)}"
    return f"{letters}-{digits}"


def poisson_disk_3d(count, radius, bounds, existing=None):
    """Generate roughly evenly-spaced points in 3D space."""
    points = list(existing) if existing else []
    attempts = 0
    max_attempts = count * 30
    while len(points) < count + (len(existing) if existing else 0) and attempts < max_attempts:
        x = random.uniform(-bounds, bounds)
        y = random.uniform(-bounds, bounds)
        z = random.uniform(-bounds * 0.3, bounds * 0.3)  # Flatter galaxy
        # Check minimum distance
        too_close = False
        for px, py, pz in points:
            dist = math.sqrt((x - px)**2 + (y - py)**2 + (z - pz)**2)
            if dist < radius:
                too_close = True
                break
        if not too_close:
            points.append((x, y, z))
        attempts += 1
    return points


def build_connections(systems, max_dist=120, max_connections=6, min_connections=2):
    """Build jump gate network. Ensures fully connected graph (no islands).
    Max 5 for high/med-sec, max 3 for null-sec. Dead-ends allowed but no orphans."""
    connections = {sid: [] for sid in systems}
    positions = {sid: (s['x'], s['y'], s['z']) for sid, s in systems.items()}
    
    def max_for(sid):
        sec = systems[sid]['security']
        if sec in ('high', 'medium'):
            return 5
        return 3
    
    sids = list(systems.keys())
    
    # Phase 1: Connect each system to its nearest neighbor(s) within range
    for sid1 in sids:
        cap = max_for(sid1)
        if len(connections[sid1]) >= cap:
            continue
        distances = []
        for sid2 in sids:
            if sid1 == sid2:
                continue
            p1, p2 = positions[sid1], positions[sid2]
            dist = math.sqrt(sum((a - b)**2 for a, b in zip(p1, p2)))
            if dist <= max_dist:
                distances.append((dist, sid2))
        distances.sort()
        
        for dist, sid2 in distances:
            if len(connections[sid1]) >= cap:
                break
            if len(connections[sid2]) >= max_for(sid2):
                continue
            if sid2 not in connections[sid1]:
                connections[sid1].append(sid2)
                connections[sid2].append(sid1)
    
    # Phase 2: Ensure every system has at least 1 connection
    for sid in sids:
        if len(connections[sid]) == 0:
            distances = [(math.sqrt(sum((a-b)**2 for a,b in zip(positions[sid],positions[s2]))), s2) for s2 in sids if s2 != sid]
            distances.sort()
            sid2 = distances[0][1]
            connections[sid].append(sid2)
            connections[sid2].append(sid)
    
    # Phase 3: Ensure full graph connectivity (merge isolated components)
    def bfs_component(start):
        visited = set()
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            for neighbor in connections[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
        return visited
    
    visited_all = set()
    components = []
    for sid in sids:
        if sid not in visited_all:
            comp = bfs_component(sid)
            components.append(comp)
            visited_all.update(comp)
    
    # Connect components by finding nearest pair between each component and the largest
    if len(components) > 1:
        components.sort(key=len, reverse=True)
        main_comp = components[0]
        for comp in components[1:]:
            best_dist = float('inf')
            best_pair = None
            for s1 in comp:
                for s2 in main_comp:
                    d = math.sqrt(sum((a-b)**2 for a,b in zip(positions[s1], positions[s2])))
                    if d < best_dist:
                        best_dist = d
                        best_pair = (s1, s2)
            if best_pair:
                s1, s2 = best_pair
                connections[s1].append(s2)
                connections[s2].append(s1)
                main_comp.update(comp)
        print(f"  Merged {len(components)-1} isolated components into main graph")
    
    return connections


def determine_security(x, y, z, faction_id):
    """Security based on distance from center and faction."""
    dist_from_center = math.sqrt(x**2 + y**2 + z**2)
    if faction_id == 'corsairs':
        return 'none'
    if dist_from_center < 200:
        return 'high'
    elif dist_from_center < 400:
        return 'medium'
    elif dist_from_center < 600:
        return 'low'
    return 'none'


def determine_ore_fields(security, system_type):
    """Assign asteroid fields based on security level."""
    fields = []
    if system_type not in ('mining', 'frontier', 'processing', 'industrial'):
        if random.random() < 0.3:  # 30% chance of incidental belt
            fields.append(('common', random.uniform(0.5, 1.5)))
        return fields
    
    if security in ('high', 'medium'):
        fields.append(('common', random.uniform(1.0, 3.0)))
        if random.random() < 0.4:
            fields.append(('common', random.uniform(0.5, 1.5)))
    if security in ('medium', 'low'):
        fields.append(('uncommon', random.uniform(0.8, 2.0)))
        if random.random() < 0.3:
            fields.append(('rare', random.uniform(0.5, 1.5)))
    if security in ('low', 'none'):
        fields.append(('rare', random.uniform(1.0, 2.5)))
        if random.random() < 0.4:
            fields.append(('exotic', random.uniform(0.5, 1.5)))
    if security == 'none':
        if random.random() < 0.15:
            fields.append(('anomalous', random.uniform(0.3, 1.0)))
    
    return fields


# Ore types by category
ORE_CATEGORIES = {
    'common': ['iron_ore', 'copper_ore', 'carbonite', 'hydral_ice', 'silicon_ore', 'calcite'],
    'uncommon': ['cobalt_ore', 'zinc_ore', 'tin_ore', 'nickel_ore', 'nitrogen_ice', 'methane_ice', 'biomass'],
    'rare': ['titanium_ore', 'tungsten_ore', 'chromium_ore', 'helium3', 'xenon_gas', 'spore_clusters', 'amino_gel'],
    'exotic': ['platinum_ore', 'gold_ore', 'palladium_ore', 'quartz_crystal', 'lithium_crystal', 'beryllium_crystal'],
    'anomalous': ['kraxolite', 'void_shard', 'neutronium'],
}


def generate_universe():
    """Generate the full 2,500 system universe."""
    systems = {}
    name_idx = 0
    
    print("Generating faction homeworld clusters...")
    # Generate faction core systems
    for fid, fdata in FACTIONS.items():
        fx, fy, fz = fdata['pos']
        count = fdata['systems']
        
        # Generate positions around faction center
        for i in range(count):
            if name_idx < len(CORE_NAMES):
                name = CORE_NAMES[name_idx]
                name_idx += 1
            else:
                name = generate_null_sec_name()
            
            # Scatter around faction center
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(10, 150)
            x = fx + r * math.cos(angle) + random.uniform(-20, 20)
            y = fy + r * math.sin(angle) + random.uniform(-20, 20)
            z = fz + random.uniform(-30, 30)
            
            sid = name.lower().replace(' ', '_').replace("'", "").replace('-', '_')
            # Ensure unique
            while sid in systems:
                sid = sid + '_' + str(random.randint(1, 99))
            
            security = determine_security(x, y, z, fid)
            sys_type = random.choice(SYSTEM_TYPES_CLAIMED)
            
            systems[sid] = {
                'name': name, 'x': round(x, 1), 'y': round(y, 1), 'z': round(z, 1),
                'system_type': sys_type, 'security': security, 'faction_id': fid,
                'cluster': fdata['name'],
            }
    
    print(f"  Generated {len(systems)} faction systems")
    
    # Generate remaining null-sec systems
    print("Generating null-sec systems...")
    existing_positions = [(s['x'], s['y'], s['z']) for s in systems.values()]
    target_total = 2500
    remaining = target_total - len(systems)
    
    # Use a looser spacing for the wild systems - SPHERICAL distribution
    radius_max = 1200
    min_spacing = 40
    
    null_positions = []
    attempts = 0
    while len(null_positions) < remaining and attempts < remaining * 50:
        # Spherical distribution (slightly flattened)
        r = random.uniform(100, radius_max) * (random.random() ** 0.33)  # cube root for uniform volume
        theta = random.uniform(0, 2 * math.pi)
        phi = random.uniform(-0.4, 0.4)  # flatten z
        x = r * math.cos(theta) * math.cos(phi)
        y = r * math.sin(theta) * math.cos(phi)
        z = r * math.sin(phi) * 0.3  # extra flatten
        
        # Check against all existing
        too_close = False
        for px, py, pz in existing_positions + null_positions:
            dist = math.sqrt((x - px)**2 + (y - py)**2 + (z - pz)**2)
            if dist < min_spacing:
                too_close = True
                break
        if not too_close:
            null_positions.append((x, y, z))
        attempts += 1
        
        if attempts % 10000 == 0:
            print(f"  ...{len(null_positions)}/{remaining} placed ({attempts} attempts)")
    
    print(f"  Generated {len(null_positions)} null-sec positions")
    
    # Create null-sec system entries with constellation names
    CONSTELLATIONS = [
        'Outer Reach', 'Void Expanse', 'Dark Nebula', 'Shattered Rim',
        'Ghost Sector', 'Iron Veil', 'Crimson Drift', 'Silent Deep',
        'Ember Fields', 'Frozen Wake', 'Obsidian Cluster', 'Tempest Zone',
        'Serpent Arm', 'Dead Light', 'Ashen Corridor', 'Wraith Nebula',
        'Storm Front', 'Hollow Stars', 'Burning Edge', 'Pale Expanse',
        'Shadow Reach', 'Broken Chain', 'Rust Belt', 'Nova Remnant',
    ]
    used_names = set()
    for x, y, z in null_positions:
        name = generate_null_sec_name()
        while name in used_names:
            name = generate_null_sec_name()
        used_names.add(name)
        
        sid = name.lower().replace('-', '_')
        dist_from_center = math.sqrt(x**2 + y**2 + z**2)
        
        if dist_from_center < 400:
            security = 'low'
        elif dist_from_center < 700:
            security = random.choice(['low', 'none'])
        else:
            security = 'none'
        
        # Assign constellation based on angular sector
        angle = math.atan2(y, x)
        sector_idx = int((angle + math.pi) / (2 * math.pi) * len(CONSTELLATIONS))
        sector_idx = min(sector_idx, len(CONSTELLATIONS) - 1)
        constellation = CONSTELLATIONS[sector_idx]
        
        sys_type = random.choice(SYSTEM_TYPES_WILD)
        
        systems[sid] = {
            'name': name, 'x': round(x, 1), 'y': round(y, 1), 'z': round(z, 1),
            'system_type': sys_type, 'security': security, 'faction_id': '',
            'cluster': constellation,
        }
    
    print(f"Total systems: {len(systems)}")
    
    # Build connections
    print("Building jump gate network...")
    connections = build_connections(systems, max_dist=100, max_connections=5, min_connections=2)
    
    total_connections = sum(len(v) for v in connections.values()) // 2
    avg_connections = sum(len(v) for v in connections.values()) / len(systems)
    print(f"  Total connections: {total_connections}")
    print(f"  Average connections per system: {avg_connections:.1f}")
    
    # Generate asteroid fields
    print("Generating asteroid fields...")
    asteroid_fields = {}
    field_yields = {}
    field_id_counter = 0
    
    for sid, sys in systems.items():
        fields = determine_ore_fields(sys['security'], sys['system_type'])
        for category, density in fields:
            field_id_counter += 1
            fid = f"field_{field_id_counter:05d}"
            
            # Pick 2-4 ores from the category
            ores = random.sample(ORE_CATEGORIES[category], min(random.randint(2, 4), len(ORE_CATEGORIES[category])))
            
            field_name = f"{sys['name']} {category.title()} Belt"
            asteroid_fields[fid] = {
                'name': field_name, 'system_id': sid,
                'field_type': category, 'density': round(density, 2),
                'danger': 0.0 if sys['security'] == 'high' else 0.3 if sys['security'] == 'medium' else 0.6 if sys['security'] == 'low' else 0.9,
            }
            field_yields[fid] = ores
    
    print(f"  Generated {len(asteroid_fields)} asteroid fields")
    
    return systems, connections, asteroid_fields, field_yields


def write_to_db(systems, connections, asteroid_fields, field_yields):
    """Write generated universe to game_data.db."""
    conn = sqlite3.connect(DB)
    
    # Clear existing universe data
    conn.execute("DELETE FROM system_connections")
    conn.execute("DELETE FROM field_yields")
    conn.execute("DELETE FROM asteroid_fields")
    conn.execute("DELETE FROM system_objects")
    conn.execute("DELETE FROM station_produces")
    conn.execute("DELETE FROM stations")
    conn.execute("DELETE FROM systems")
    
    print("Writing systems...")
    for sid, s in systems.items():
        conn.execute("""INSERT INTO systems (id, name, system_type, cluster, security, faction_id, x, y, z)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sid, s['name'], s['system_type'], s['cluster'], s['security'], s['faction_id'], s['x'], s['y'], s['z']))
    
    print("Writing connections...")
    written_conns = set()
    for sid, targets in connections.items():
        for tid in targets:
            pair = tuple(sorted([sid, tid]))
            if pair not in written_conns:
                conn.execute("INSERT INTO system_connections (from_id, to_id) VALUES (?, ?)", (sid, tid))
                conn.execute("INSERT INTO system_connections (from_id, to_id) VALUES (?, ?)", (tid, sid))
                written_conns.add(pair)
    
    print("Writing asteroid fields...")
    for fid, f in asteroid_fields.items():
        conn.execute("""INSERT INTO asteroid_fields (id, name, system_id, field_type, density, danger)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (fid, f['name'], f['system_id'], f['field_type'], f['density'], f['danger']))
        for ore_id in field_yields[fid]:
            conn.execute("INSERT INTO field_yields (field_id, commodity_id) VALUES (?, ?)", (fid, ore_id))
    
    # Generate stations for faction systems
    print("Writing stations...")
    station_count = 0
    # Station types and what they produce by system_type
    STATION_PRODUCES = {
        'industrial': ['steel_plate', 'titanium_alloy', 'carbon_composite', 'ceramic_plate'],
        'mining': [],  # Mining colonies don't produce refined goods (miners do)
        'trade': [],
        'processing': ['refined_iron', 'refined_copper', 'refined_titanium', 'hydrogen_fuel'],
        'shipyard': ['std_engine', 'armor_plates', 'shield_generator'],
        'military': ['pulse_laser', 'railgun', 'autocannon', 'missile_launcher'],
        'agricultural': ['processed_protein', 'purified_water', 'bio_catalyst'],
    }
    
    for sid, s in systems.items():
        if not s['faction_id']:
            continue  # No stations in unclaimed systems
        
        # 1-3 stations per faction system
        num_stations = 1 if s['security'] == 'low' else 2 if s['security'] == 'medium' else random.randint(2, 3)
        
        for i in range(num_stations):
            station_count += 1
            st_id = f"st_{station_count:05d}"
            
            if i == 0:
                st_type = s['system_type']
                st_name = f"{s['name']} {st_type.replace('_', ' ').title()}"
            else:
                st_type = random.choice(['trade', 'processing', 'industrial'])
                st_name = f"{s['name']} {['Hub', 'Depot', 'Works', 'Market', 'Outpost'][i % 5]}"
            
            rate = 1.0 if s['security'] == 'high' else 0.7 if s['security'] == 'medium' else 0.4
            conn.execute("INSERT INTO stations (id, name, system_id, station_type, production_rate) VALUES (?,?,?,?,?)",
                         (st_id, st_name, sid, st_type, rate))
            
            # Assign production
            produces = STATION_PRODUCES.get(st_type, [])
            if produces:
                for prod_id in random.sample(produces, min(2, len(produces))):
                    conn.execute("INSERT INTO station_produces (station_id, commodity_id) VALUES (?,?)", (st_id, prod_id))
    
    print(f"  Generated {station_count} stations")
    
    conn.commit()
    conn.close()
    print("Done!")


def print_stats(systems, connections, asteroid_fields):
    """Print universe statistics."""
    print("\n=== UNIVERSE STATS ===")
    print(f"Total systems: {len(systems)}")
    
    # By security
    sec_counts = {}
    for s in systems.values():
        sec_counts[s['security']] = sec_counts.get(s['security'], 0) + 1
    print(f"By security: {sec_counts}")
    
    # By faction
    fac_counts = {}
    for s in systems.values():
        f = s['faction_id'] or 'unclaimed'
        fac_counts[f] = fac_counts.get(f, 0) + 1
    print(f"By faction: {fac_counts}")
    
    # Connections
    conn_counts = [len(v) for v in connections.values()]
    print(f"Connections: min={min(conn_counts)}, max={max(conn_counts)}, avg={sum(conn_counts)/len(conn_counts):.1f}")
    
    # Fields
    print(f"Asteroid fields: {len(asteroid_fields)}")
    type_counts = {}
    for f in asteroid_fields.values():
        type_counts[f['field_type']] = type_counts.get(f['field_type'], 0) + 1
    print(f"By type: {type_counts}")


if __name__ == "__main__":
    systems, connections, asteroid_fields, field_yields = generate_universe()
    print_stats(systems, connections, asteroid_fields)
    
    print("\nWriting to database...")
    write_to_db(systems, connections, asteroid_fields, field_yields)
    print("\nUniverse generated successfully!")
