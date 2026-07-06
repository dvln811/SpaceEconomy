"""Regenerate station names with Corp + Type + Roman Numeral format.
Example: 'Ironveil Foundry II', 'Nexus Industries Trade Hub VII'"""
import sqlite3
import random
random.seed(42)

DB = 'data/game_data.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Get all corporations for naming
corps = conn.execute("SELECT id, name FROM corporations").fetchall()
if not corps:
    # Fallback corp names if no corps table
    corp_names = ['Ironveil', 'Nexus Industries', 'Kestrel Corp', 'Vanguard Systems', 
                  'Obsidian Works', 'Nova Dynamics', 'Apex Manufacturing', 'Zenith Corp',
                  'Stellaris Holdings', 'Forge Industries', 'Crimson Fleet', 'Azure Trading',
                  'Titan Engineering', 'Meridian Corp', 'Solaris Group']
else:
    corp_names = [c['name'] for c in corps]

print(f"Using {len(corp_names)} corporation names")

# Station types based on station_type field
TYPE_NAMES = {
    'trade_hub': 'Trade Hub',
    'military_base': 'Military Base', 
    'shipyard': 'Shipyard',
    'factory': 'Fabrication Plant',
    'refinery': 'Refinery',
    'component_works': 'Component Works',
    'mining_colony': 'Mining Colony',
}

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']

# Get all stations with their system info
stations = conn.execute("""
    SELECT s.id, s.name, s.system_id, s.station_type,
           so.distance
    FROM stations s
    LEFT JOIN system_objects so ON so.station_id = s.id
    ORDER BY s.system_id, so.distance
""").fetchall()

# Group by system and assign Roman numerals by distance order
from collections import defaultdict
system_stations = defaultdict(list)
for st in stations:
    system_stations[st['system_id']].append(st)

updated = 0
for sys_id, sys_stations in system_stations.items():
    # Sort by distance from star
    sys_stations.sort(key=lambda x: x['distance'] or 0)
    
    for i, st in enumerate(sys_stations):
        numeral = ROMAN[i] if i < len(ROMAN) else str(i+1)
        corp = random.choice(corp_names)
        stype = TYPE_NAMES.get(st['station_type'], 'Station')
        new_name = f"{corp} {stype} {numeral}"
        
        # Update station name
        conn.execute("UPDATE stations SET name=? WHERE id=?", (new_name, st['id']))
        # Also update the system_objects entry
        conn.execute("UPDATE system_objects SET name=? WHERE station_id=?", (new_name, st['id']))
        updated += 1

conn.commit()
conn.close()
print(f"Renamed {updated} stations across {len(system_stations)} systems")
# Show some examples
conn = sqlite3.connect(DB)
examples = conn.execute("SELECT name, system_id FROM stations WHERE system_id='rigel' ORDER BY name").fetchall()
print("\nRigel stations:")
for e in examples:
    print(f"  {e[0]}")
conn.close()
