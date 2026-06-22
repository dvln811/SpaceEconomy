"""Merge ship_types and military_ships into a single 'ships' table."""
import sqlite3, json, os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

def merge():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Create unified ships table
    conn.execute("""CREATE TABLE IF NOT EXISTS ships (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        hull_class TEXT NOT NULL DEFAULT '',
        faction_id TEXT DEFAULT '',
        tier INTEGER DEFAULT 1,
        hull_hp INTEGER DEFAULT 100,
        armor_hp INTEGER DEFAULT 0,
        shield_hp INTEGER DEFAULT 0,
        cargo_capacity INTEGER DEFAULT 0,
        fuel_capacity INTEGER DEFAULT 100,
        speed REAL DEFAULT 1.0,
        intra_speed REAL DEFAULT 0.2,
        align_time INTEGER DEFAULT 5,
        crew INTEGER DEFAULT 1,
        hardpoints TEXT DEFAULT '{}',
        weapons TEXT DEFAULT '[]',
        modules TEXT DEFAULT '[]',
        build_cost TEXT DEFAULT '{}',
        build_time INTEGER DEFAULT 0,
        description TEXT DEFAULT ''
    )""")

    # Migrate civilian ships
    civs = conn.execute("SELECT * FROM ship_types").fetchall()
    for s in civs:
        hp = json.loads(s['hardpoints']) if s['hardpoints'] else {}
        conn.execute("""INSERT OR REPLACE INTO ships 
            (id, name, hull_class, faction_id, tier, hull_hp, armor_hp, shield_hp,
             cargo_capacity, fuel_capacity, speed, intra_speed, align_time, crew,
             hardpoints, weapons, modules, build_cost, build_time, description)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (s['id'], s['name'], s['role'], '', s['tier'],
             s['hull_hp'], 0, 0,
             s['cargo_capacity'], s['fuel_capacity'], s['speed'], s['intra_speed'],
             s['align_time'], 1,
             s['hardpoints'], '[]', '[]',
             s['build_cost'], s['build_time'] or 0, s['description']))

    # Migrate military ships
    mils = conn.execute("SELECT * FROM military_ships").fetchall()
    for s in mils:
        conn.execute("""INSERT OR REPLACE INTO ships
            (id, name, hull_class, faction_id, tier, hull_hp, armor_hp, shield_hp,
             cargo_capacity, fuel_capacity, speed, intra_speed, align_time, crew,
             hardpoints, weapons, modules, build_cost, build_time, description)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (s['id'], s['name'], s['hull_class'], s['faction_id'],
             # Tier based on hull class
             {'fighter':1,'frigate':2,'destroyer':3,'cruiser':4,'battlecruiser':5,'battleship':6,'carrier':7,'dreadnought':8}.get(s['hull_class'], 3),
             s['hull_hp'], s['armor_hp'], s['shield_hp'],
             0, 100, 1.0, 0.2, 5, s['crew'],
             s['hardpoints'] or '{}', s['weapons'], s['modules'],
             s['build_cost'], s['build_time'] or 0, s['description']))

    conn.commit()

    # Verify
    total = conn.execute("SELECT COUNT(*) FROM ships").fetchone()[0]
    by_class = conn.execute("SELECT hull_class, COUNT(*) FROM ships GROUP BY hull_class ORDER BY hull_class").fetchall()
    print(f"Merged into 'ships' table: {total} total")
    for r in by_class:
        print(f"  {r[0]}: {r[1]}")

    conn.close()

if __name__ == '__main__':
    merge()
