import sqlite3
conn = sqlite3.connect('data/game_data.db')

# Current military_base consumption
rows = conn.execute("SELECT * FROM station_consumption WHERE station_type='military_base'").fetchall()
print("Current military_base consumption:")
for r in rows: print(f"  {r[1]}")

print()
rows = conn.execute("SELECT * FROM station_consumption WHERE station_type='shipyard'").fetchall()
print("Current shipyard consumption:")
for r in rows: print(f"  {r[1]}")

# Sample weapon IDs by group
print("\nWeapon groups (for military consumption):")
rows = conn.execute("SELECT DISTINCT group_name FROM commodities WHERE category='Weapons'").fetchall()
for r in rows: print(f"  {r[0]}")

# Get a few weapon IDs (standard quality, M size - representative)
print("\nSample M-size standard weapons:")
rows = conn.execute("SELECT id, name FROM commodities WHERE category='Weapons' AND stats LIKE '%Standard%' AND stats LIKE '%\"M\"%'").fetchall()
for r in rows: print(f"  {r[0]:45s} {r[1]}")

# Ammo groups
print("\nAmmo subcategories:")
rows = conn.execute("SELECT subcategory, COUNT(*) FROM commodities WHERE category='Ammunition' GROUP BY subcategory").fetchall()
for r in rows: print(f"  {r[0]:25s} {r[1]}")

# Sample ammo IDs
print("\nSample ammo (first of each subcategory):")
rows = conn.execute("SELECT id, name, subcategory FROM commodities WHERE category='Ammunition' GROUP BY subcategory").fetchall()
for r in rows: print(f"  {r[0]:50s} {r[1]}")

# Hull components
print("\nComponent IDs available:")
rows = conn.execute("SELECT id, name FROM commodities WHERE subcategory='Components' AND volume <= 1.5 ORDER BY name").fetchall()
for r in rows: print(f"  {r[0]:30s} {r[1]}")

# Fuel IDs
print("\nFuel-related items:")
rows = conn.execute("SELECT id, name FROM commodities WHERE name LIKE '%fuel%' OR name LIKE '%Fuel%' OR id LIKE '%fuel%'").fetchall()
for r in rows: print(f"  {r[0]:30s} {r[1]}")

conn.close()
