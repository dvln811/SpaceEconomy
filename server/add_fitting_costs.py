"""Add cpu_cost and pg_cost to stats JSON for all Ship Equipment and Weapons."""
import sqlite3, json, os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'game_data.db')
conn = sqlite3.connect(DB)

# Fitting costs: group_name -> {size -> (cpu, pg)}
WEAPON_COSTS = {
    'Autocannons':        {'S':(8,5),   'M':(18,12), 'L':(30,25), 'C':(50,45)},
    'Autocannon':         {'S':(8,5),   'M':(18,12), 'L':(30,25), 'C':(50,45)},
    'Railguns':           {'S':(20,8),  'M':(35,18), 'L':(55,35), 'C':(80,60)},
    'Railgun':            {'S':(20,8),  'M':(35,18), 'L':(55,35), 'C':(80,60)},
    'Beam Lasers':        {'S':(12,12), 'M':(25,25), 'L':(40,45), 'C':(65,75)},
    'Beam Laser':         {'S':(12,12), 'M':(25,25), 'L':(40,45), 'C':(65,75)},
    'Pulse Lasers':       {'S':(10,8),  'M':(20,18), 'L':(35,32), 'C':(55,55)},
    'Pulse Laser':        {'S':(10,8),  'M':(20,18), 'L':(35,32), 'C':(55,55)},
    'Blasters':           {'S':(10,10), 'M':(22,22), 'L':(38,40), 'C':(60,65)},
    'Blaster':            {'S':(10,10), 'M':(22,22), 'L':(38,40), 'C':(60,65)},
    'Gauss Cannons':      {'S':(22,10), 'M':(38,20), 'L':(58,38), 'C':(85,65)},
    'Gauss Cannon':       {'S':(22,10), 'M':(38,20), 'L':(58,38), 'C':(85,65)},
    'Artillery':          {'S':(15,8),  'M':(28,16), 'L':(45,30), 'C':(70,50)},
    'Missile Launchers':  {'S':(25,5),  'M':(40,12), 'L':(60,22), 'C':(90,40)},
    'Missile Launcher':   {'S':(25,5),  'M':(40,12), 'L':(60,22), 'C':(90,40)},
    'Rocket Launchers':   {'S':(20,4),  'M':(32,8),  'L':(48,16), 'C':(72,30)},
    'Rocket Launcher':    {'S':(20,4),  'M':(32,8),  'L':(48,16), 'C':(72,30)},
    'Torpedo Launchers':  {'S':(30,8),  'M':(48,16), 'L':(70,28), 'C':(100,50)},
    'Torpedo Launcher':   {'S':(30,8),  'M':(48,16), 'L':(70,28), 'C':(100,50)},
    'Plasma Cannons':     {'S':(14,14), 'M':(28,28), 'L':(45,50), 'C':(70,80)},
    'Plasma Cannon':      {'S':(14,14), 'M':(28,28), 'L':(45,50), 'C':(70,80)},
    'Flak Batteries':     {'S':(6,3),   'M':(12,6),  'L':(20,12), 'C':(35,22)},
    'Flak Battery':       {'S':(6,3),   'M':(12,6),  'L':(20,12), 'C':(35,22)},
}

MID_COSTS = {
    'Shield Boosters':    {'S':(20,15), 'M':(35,30), 'L':(55,55)},
    'Shield Extenders':   {'S':(25,20), 'M':(40,35), 'L':(60,55)},
    'Shield Hardeners':   {'S':(20,1),  'M':(30,1),  'L':(45,1)},
    'Shield Rechargers':  {'S':(15,1),  'M':(25,1),  'L':(40,1)},
    'Afterburners':       {'S':(10,15), 'M':(18,30), 'L':(28,55)},
    'Microwarpdrives':    {'S':(15,25), 'M':(25,50), 'L':(40,90)},
    'Overdrive Injectors':{'S':(8,5),   'M':(15,10), 'L':(22,18)},
    'ECM':                {'S':(30,1),  'M':(50,1),  'L':(75,1)},
    'Sensor Dampeners':   {'S':(25,1),  'M':(40,1),  'L':(60,1)},
    'Target Painters':    {'S':(20,1),  'M':(35,1),  'L':(50,1)},
    'Tracking Disruptors':{'S':(25,1),  'M':(40,1),  'L':(60,1)},
    'Stasis Webifiers':   {'S':(20,1),  'M':(35,1),  'L':(55,1)},
    'Warp Disruptors':    {'S':(20,1),  'M':(30,1),  'L':(45,1)},
    'Warp Scramblers':    {'S':(25,1),  'M':(40,1),  'L':(60,1)},
    'Capacitor Boosters': {'S':(10,5),  'M':(18,10), 'L':(28,18)},
    'Capacitor Batteries':{'S':(12,5),  'M':(20,10), 'L':(30,18)},
    'Capacitor Rechargers':{'S':(15,1), 'M':(25,1),  'L':(40,1)},
    'Scanners':           {'S':(20,3),  'M':(35,5),  'L':(50,8)},
    'Cloaking Devices':   {'S':(50,1),  'M':(75,1),  'L':(100,1)},
    'Tractor Beams':      {'S':(15,5),  'M':(25,10), 'L':(40,18)},
    'Salvagers':          {'S':(15,3),  'M':(25,5),  'L':(40,8)},
}

LOW_COSTS = {
    'Armor Plates':       {'S':(5,15),  'M':(8,30),  'L':(12,55)},
    'Armor Repairers':    {'S':(10,12), 'M':(18,25), 'L':(28,45)},
    'Armor Hardeners':    {'S':(15,1),  'M':(25,1),  'L':(40,1)},
    'Damage Control':     {'S':(10,5),  'M':(15,8),  'L':(22,12)},
    'Cargo Expanders':    {'S':(15,1),  'M':(25,1),  'L':(40,1)},
    'Co-Processors':      {'S':(1,5),   'M':(1,10),  'L':(1,18)},
    'Reactor Controls':   {'S':(5,1),   'M':(8,1),   'L':(12,1)},
    'Power Diagnostics':  {'S':(8,1),   'M':(12,1),  'L':(18,1)},
    'Inertial Stabilizers':{'S':(12,1), 'M':(20,1),  'L':(30,1)},
    'Nanofiber Structures':{'S':(10,1), 'M':(18,1),  'L':(28,1)},
    'Warp Stabilizers':   {'S':(15,1),  'M':(25,1),  'L':(40,1)},
    'Drone Control Units':{'S':(25,5),  'M':(40,10), 'L':(60,18)},
    'Mining Upgrades':    {'S':(15,3),  'M':(25,5),  'L':(40,8)},
}

HIGH_UTILITY_COSTS = {
    'Mining Lasers':      {'S':(10,5),  'M':(20,12), 'L':(35,22)},
    'Strip Miners':       {'S':(15,8),  'M':(28,16), 'L':(45,28)},
    'Ice Harvesters':     {'S':(12,6),  'M':(22,14), 'L':(38,24)},
    'Gas Harvesters':     {'S':(10,5),  'M':(18,10), 'L':(30,18)},
    'Energy Neutralizers':{'S':(20,10), 'M':(35,20), 'L':(55,35)},
    'Energy Nosferatu':   {'S':(15,8),  'M':(28,16), 'L':(45,28)},
    'Remote Armor Repairers':{'S':(20,15), 'M':(35,30), 'L':(55,50)},
    'Remote Shield Boosters':{'S':(25,12), 'M':(40,25), 'L':(60,45)},
}

# Quality modifiers for fitting cost
QUALITY_MOD = {
    'Standard': 1.00,
    'Named': 0.85,
    'T2': 1.20,
    'Faction': 0.90,
}

# Combine all lookup tables
ALL_COSTS = {}
ALL_COSTS.update(WEAPON_COSTS)
ALL_COSTS.update(MID_COSTS)
ALL_COSTS.update(LOW_COSTS)
ALL_COSTS.update(HIGH_UTILITY_COSTS)

# Process all relevant items
rows = conn.execute(
    "SELECT id, name, group_name, stats FROM commodities WHERE category IN ('Ship Equipment', 'Weapons')"
).fetchall()

updated = 0
missed = 0
missed_groups = set()

for row in rows:
    item_id, name, group_name, stats_str = row
    stats = json.loads(stats_str) if stats_str else {}
    size = stats.get('size', 'S')
    quality = stats.get('quality', 'Standard')

    # Lookup base cost
    costs = ALL_COSTS.get(group_name)
    if not costs:
        missed += 1
        missed_groups.add(group_name)
        continue

    base = costs.get(size)
    if not base:
        # Try falling back to smallest available
        base = costs.get('S', (15, 8))

    cpu_base, pg_base = base
    mod = QUALITY_MOD.get(quality, 1.0)

    stats['cpu_cost'] = round(cpu_base * mod)
    stats['pg_cost'] = round(pg_base * mod)

    conn.execute('UPDATE commodities SET stats=? WHERE id=?', (json.dumps(stats), item_id))
    updated += 1

conn.commit()

print(f'Updated {updated} items with cpu_cost/pg_cost')
if missed:
    print(f'Skipped {missed} items (no cost mapping for groups: {sorted(missed_groups)})')

# Verify a sample
print('\n--- Sample verification ---')
sample = conn.execute(
    "SELECT name, group_name, stats FROM commodities WHERE category IN ('Ship Equipment','Weapons') AND stats LIKE '%cpu_cost%' LIMIT 12"
).fetchall()
for s in sample:
    st = json.loads(s[2])
    print(f'  {s[0]:35s} {s[1]:25s} CPU:{st.get("cpu_cost"):>3} PG:{st.get("pg_cost"):>3} [{st.get("size","?")} {st.get("quality","?")}]')

conn.close()
