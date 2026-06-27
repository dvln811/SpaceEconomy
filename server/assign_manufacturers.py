"""Remove prototype ships, assign manufacturers, set cargo capacities."""
import sqlite3, json, os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'game_data.db')
conn = sqlite3.connect(DB)

# --- 1. Remove Viper Interceptor and Warden Frigate ---
print("Removing Viper Interceptor and Warden Frigate...")
conn.execute("DELETE FROM ships WHERE id='viper_interceptor'")
conn.execute("DELETE FROM ships WHERE id='warden_frigate'")
print(f"  Deleted {conn.total_changes} ships")

# --- 2. Add manufacturer column and assign shipyards ---
existing = [r[1] for r in conn.execute('PRAGMA table_info(ships)').fetchall()]
if 'manufacturer' not in existing:
    conn.execute("ALTER TABLE ships ADD COLUMN manufacturer TEXT DEFAULT ''")
    print("  Added manufacturer column")

# Shipyard assignments per faction
# Pick the most fitting corp per faction for ship construction
FACTION_SHIPYARDS = {
    'terran_fed': 'Apex Fleet',
    'free_states': 'Nova Logistics',
    'iron_compact': 'Meridian Collective',
    'merchants_guild': 'Talon Solutions',
    'science_collective': 'Citadel Syndicate',
    'corsairs': 'Black Shipwrights',
}
# Civilian ships get a universal manufacturer
CIVILIAN_MANUFACTURER = 'Frontier Shipworks'

rows = conn.execute('SELECT id, faction_id FROM ships').fetchall()
for r in rows:
    sid, fid = r
    if fid and fid in FACTION_SHIPYARDS:
        mfg = FACTION_SHIPYARDS[fid]
    else:
        mfg = CIVILIAN_MANUFACTURER
    conn.execute('UPDATE ships SET manufacturer=? WHERE id=?', (mfg, sid))

print(f"  Assigned manufacturers to {len(rows)} ships")

# --- 3. Set cargo capacities by hull class ---
# Reasonable cargo per class (m3)
CARGO_BY_CLASS = {
    'Fighter':       15,
    'Frigate':       50,
    'Destroyer':     120,
    'Cruiser':       300,
    'Battlecruiser': 500,
    'Battleship':    800,
    'Carrier':       2500,
    'Dreadnought':   1500,
    'Industrial':    None,  # keep existing (already scaled by tier)
    'Mining Barge':  None,  # keep existing
}

rows = conn.execute('SELECT id, hull_class, cargo_capacity FROM ships').fetchall()
updated = 0
for r in rows:
    sid, hc, existing_cargo = r
    target = CARGO_BY_CLASS.get(hc)
    if target is None:
        continue  # keep existing for industrials/miners
    conn.execute('UPDATE ships SET cargo_capacity=? WHERE id=?', (target, sid))
    updated += 1

print(f"  Set cargo capacity for {updated} combat ships")

conn.commit()

# Verify
print("\n--- Verification ---")
rows = conn.execute('SELECT name, hull_class, manufacturer, cargo_capacity, speed FROM ships ORDER BY hull_class, name LIMIT 25').fetchall()
for r in rows:
    print(f"  {r[1]:15s} {r[0]:20s} mfg:{r[2]:25s} cargo:{r[3]:>5} spd:{int(r[4])}")

conn.close()
