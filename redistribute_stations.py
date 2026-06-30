"""Redistribute stations: keep ~535-600 total, just move to proper sec levels."""
import sqlite3
import random
import json

conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row

systems = conn.execute("SELECT id, name, sec_level, faction_id FROM systems WHERE faction_id != ''").fetchall()
print(f"{len(systems)} faction systems")

# Target: ~550 stations total, distributed by security
# High-sec gets more per system but fewer systems, low-sec gets less
NAMES = {
    'trade_hub': ['Exchange', 'Trade Post', 'Commerce Hub', 'Freeport'],
    'factory': ['Manufacturing', 'Industrial Hub', 'Foundry'],
    'component_works': ['Tech Lab', 'Component Works', 'Fabrication'],
    'refinery': ['Refinery', 'Processing Hub', 'Smelter'],
    'mining_colony': ['Mining Colony', 'Mining Outpost', 'Dig Site'],
    'military_base': ['Naval Station', 'Garrison', 'Fortress'],
    'shipyard': ['Shipyard', 'Drydock'],
}

HIGH_SEC_TYPES = ['trade_hub', 'factory', 'component_works', 'refinery', 'military_base', 'shipyard']
MID_SEC_TYPES = ['trade_hub', 'factory', 'refinery', 'component_works']
LOW_SEC_TYPES = ['mining_colony', 'refinery']

def gen_name(sys_name, st_type):
    return f"{sys_name} {random.choice(NAMES[st_type])}"

# Clear
conn.execute("DELETE FROM stations")
conn.execute("DELETE FROM station_produces")
conn.execute("DELETE FROM system_objects WHERE obj_type='station'")

# Budget: ~550 stations. Distribute by sec level.
# We have: 4 at 1.0, 21 at 0.9, 39 at 0.8, 75 at 0.7, 122 at 0.6, 143 at 0.5, 148 at 0.4, 221 at 0.3
# Target per-system density:
#   1.0: 5-6  (4 systems = ~22)
#   0.9: 4-5  (21 systems, pick 15 = ~65)
#   0.8: 3-4  (39 systems, pick 25 = ~85)
#   0.7: 2-3  (75 systems, pick 40 = ~100)
#   0.6: 1-2  (122 systems, pick 60 = ~100)
#   0.5: 1    (143 systems, pick 60 = ~60)
#   0.4: 0-1  (148 systems, pick 30 = ~30)
#   0.3: 0-1  (221 systems, pick 20 = ~20)
# Total: ~482 + some variance = ~520-580

station_id = 1
total = 0
by_type = {}

for sys_row in systems:
    sec = sys_row['sec_level']
    sys_id = sys_row['id']
    sys_name = sys_row['name']

    if sec >= 0.9:
        count = random.randint(4, 6)
        pool = HIGH_SEC_TYPES
        chance = 1.0
    elif sec >= 0.8:
        count = random.randint(3, 5)
        pool = HIGH_SEC_TYPES
        chance = 0.80
    elif sec >= 0.7:
        count = random.randint(2, 3)
        pool = MID_SEC_TYPES
        chance = 0.75
    elif sec >= 0.6:
        count = random.randint(1, 2)
        pool = MID_SEC_TYPES
        chance = 0.65
    elif sec >= 0.5:
        count = 1
        pool = MID_SEC_TYPES
        chance = 0.50
    elif sec >= 0.4:
        count = 1
        pool = ['mining_colony', 'mining_colony', 'refinery']
        chance = 0.45
    elif sec >= 0.3:
        count = 1
        pool = ['mining_colony']
        chance = 0.35
    elif sec >= 0.1:
        count = 1
        pool = ['mining_colony']
        chance = 0.10
    else:
        count = 0
        pool = []
        chance = 0

    if random.random() > chance:
        continue

    # Ensure trade hub in high-sec
    chosen = []
    if sec >= 0.8 and count >= 3:
        chosen.append('trade_hub')
        count -= 1
    for _ in range(count):
        chosen.append(random.choice(pool))
    # Cap shipyards
    if chosen.count('shipyard') > 1:
        for i in range(1, len(chosen)):
            if chosen[i] == 'shipyard':
                chosen[i] = 'factory'

    for st_type in chosen:
        st_id = f"st_{station_id:05d}"
        st_name = gen_name(sys_name, st_type)
        variant = random.randint(0, 5)
        conn.execute("INSERT INTO stations (id, name, system_id, station_type, production_rate, geometry_variant) VALUES (?,?,?,?,?,?)",
                     (st_id, st_name, sys_id, st_type, 3.0 if st_type == 'refinery' else 1.0, variant))
        by_type[st_type] = by_type.get(st_type, 0) + 1

        obj_id = f"obj_st_{station_id:05d}"
        dist = round(random.uniform(3, 12), 2)
        angle = round(random.uniform(0, 6.28), 4)
        conn.execute("INSERT INTO system_objects (id, name, system_id, obj_type, distance, angle, station_id) VALUES (?,?,?,?,?,?,?)",
                     (obj_id, st_name, sys_id, 'station', dist, angle, st_id))
        station_id += 1
        total += 1

conn.commit()
print(f"\nTotal: {total} stations")
print(f"By type: {json.dumps(by_type, indent=2)}")

for row in conn.execute("""SELECT round(sys.sec_level,1) as sec, count(s.id) as n, count(DISTINCT s.system_id) as sys_ct,
    printf('%.1f', 1.0*count(s.id)/count(DISTINCT s.system_id)) as avg
    FROM stations s JOIN systems sys ON s.system_id=sys.id GROUP BY sec ORDER BY sec DESC""").fetchall():
    print(f"  sec {row[0]}: {row[1]} stations in {row[2]} systems (avg {row[3]})")

conn.close()
