"""Set proper build times per docs/SHIP_BUILD_TIMES.md"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

# Military: seconds
MILITARY_TIMES = {
    'fighter': 8 * 60,          # 8 minutes
    'frigate': 22 * 60,         # 22 minutes
    'destroyer': 3 * 3600,      # 3 hours
    'cruiser': 12 * 3600,       # 12 hours
    'battlecruiser': 36 * 3600, # 1.5 days
    'battleship': 8 * 86400,    # 8 days
    'carrier': 17 * 86400,      # 17 days
    'dreadnought': 28 * 86400,  # 28 days
}

# Civilian: by ship name
CIVILIAN_TIMES = {
    'Pinto Runner': 7 * 60,
    'Mule Freighter': 8 * 60,
    'Prospect Skiff': 6 * 60,
    'Rock Hopper': 7 * 60,
    'Bison Mk.III': 90 * 60,       # 1.5 hours
    'Strip Miner': 90 * 60,
    'Excavator': 100 * 60,
    'Mammoth': 36 * 3600,           # 1.5 days
    'Ox Hauler': 36 * 3600,
    'Deep Core Borer': 36 * 3600,
    'Clydesdale': 6 * 86400,        # 6 days
    'Viper Interceptor': 90 * 60,   # 1.5 hours
    'Sentinel Corvette': 12 * 3600, # 12 hours
    'Warden Frigate': 12 * 3600,
}

conn = sqlite3.connect(DB)

# Add build_time column if missing
for table in ['military_ships', 'ship_types']:
    cols = [r[1] for r in conn.execute(f'PRAGMA table_info({table})')]
    if 'build_time' not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN build_time INTEGER DEFAULT 0")
conn.commit()

# Military ships
for hull_class, seconds in MILITARY_TIMES.items():
    conn.execute("UPDATE military_ships SET build_time=? WHERE hull_class=?", (seconds, hull_class))
    affected = conn.execute("SELECT changes()").fetchone()[0]
    print(f"  {hull_class}: {seconds}s ({seconds//3600}h) - {affected} ships")

# Civilian ships
for name, seconds in CIVILIAN_TIMES.items():
    conn.execute("UPDATE ship_types SET build_time=? WHERE name=?", (seconds, name))

# Verify
print("\nMilitary:")
for r in conn.execute("SELECT hull_class, build_time FROM military_ships GROUP BY hull_class ORDER BY build_time"):
    t = r[1]
    if t >= 86400:
        label = f"{t//86400}d"
    elif t >= 3600:
        label = f"{t//3600}h"
    else:
        label = f"{t//60}m"
    print(f"  {r[0]}: {label}")

print("\nCivilian:")
for r in conn.execute("SELECT name, build_time FROM ship_types ORDER BY build_time"):
    t = r[1]
    if t >= 86400:
        label = f"{t//86400}d"
    elif t >= 3600:
        label = f"{t//3600}h"
    else:
        label = f"{t//60}m"
    print(f"  {r[0]}: {label}")

conn.commit()
conn.close()
