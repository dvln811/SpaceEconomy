import sqlite3
conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)

# Check system_objects schema
cur.execute("PRAGMA table_info(system_objects)")
print("\nsystem_objects columns:")
for row in cur.fetchall():
    print(f"  {row[1]} ({row[2]})")

# Count
cur.execute("SELECT COUNT(*) FROM system_objects")
print(f"\nTotal system_objects: {cur.fetchone()[0]}")

# Sample orbital-ish objects
cur.execute("SELECT * FROM system_objects WHERE parent != '' LIMIT 5")
rows = cur.fetchall()
print(f"\nObjects with parent ({len(rows)} shown):")
for r in rows:
    print(f"  {dict(r)}")

# Sample stations
cur.execute("SELECT * FROM system_objects WHERE obj_type='station' LIMIT 3")
rows = cur.fetchall()
print(f"\nSample stations:")
for r in rows:
    print(f"  {dict(r)}")
