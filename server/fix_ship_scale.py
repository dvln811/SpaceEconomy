"""Fix ship build cost scaling - use class-based multipliers instead of flat 10x.

The 5x recipe multiplier already compounds through the chain (~5^4 = 625x at T5).
Ship build costs need gentler scaling, varying by hull class.
"""
import sqlite3
import json
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

# Multipliers relative to CURRENT state (which is already 10x from original)
# So we need to divide by 10 first, then apply class-based multiplier
# Original build costs -> /10 to undo -> then apply new multiplier

# Target iron ore per class (with 5x recipe scaling already in place):
# Fighter: ~20-50K -> needs multiplier ~1x on original (the 5x recipes do the work)
# Frigate: same as fighter basically
# Destroyer: ~2x original
# Cruiser: ~3-4x original  
# Battlecruiser: ~5-6x
# Battleship: ~8-10x
# Dreadnought: ~15-20x

HULL_CLASS_MULTIPLIER = {
    'fighter': 1,
    'frigate': 1,
    'destroyer': 2,
    'cruiser': 4,
    'battlecruiser': 6,
    'battleship': 10,
    'carrier': 12,
    'dreadnought': 20,
}

# Civilian ships by tier
CIV_TIER_MULTIPLIER = {
    1: 1,   # Pinto Runner, Prospect Skiff
    2: 2,   # Bison, Strip Miner
    3: 4,   # Mammoth, Ox, Excavator, Deep Core
    4: 8,   # Clydesdale
}


def fix():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Military ships: undo the 10x, apply class-based
    mil_ships = conn.execute("SELECT id, hull_class, build_cost FROM military_ships").fetchall()
    for s in mil_ships:
        bc = json.loads(s['build_cost'])
        # Undo the 10x
        bc = {k: v / 10 for k, v in bc.items()}
        # Apply class multiplier
        mult = HULL_CLASS_MULTIPLIER.get(s['hull_class'], 5)
        bc = {k: int(v * mult) for k, v in bc.items()}
        conn.execute("UPDATE military_ships SET build_cost=? WHERE id=?", (json.dumps(bc), s['id']))
    print(f"Fixed {len(mil_ships)} military ship build costs (class-based scaling)")

    # Civilian ships: undo the 10x, apply tier-based
    civ_ships = conn.execute("SELECT id, tier, build_cost FROM ship_types").fetchall()
    for s in civ_ships:
        bc = json.loads(s['build_cost'])
        # Undo the 10x
        bc = {k: v / 10 for k, v in bc.items()}
        # Apply tier multiplier
        mult = CIV_TIER_MULTIPLIER.get(s['tier'], 2)
        bc = {k: int(v * mult) for k, v in bc.items()}
        conn.execute("UPDATE ship_types SET build_cost=? WHERE id=?", (json.dumps(bc), s['id']))
    print(f"Fixed {len(civ_ships)} civilian ship build costs (tier-based scaling)")

    conn.commit()

    # Verify
    print("\n=== VERIFICATION ===")
    commodities = {}
    for row in conn.execute("SELECT * FROM commodities").fetchall():
        cid = row['id']
        recs = conn.execute("SELECT input_id, quantity FROM recipes WHERE commodity_id=?", (cid,)).fetchall()
        commodities[cid] = {'name': row['name'], 'recipe': {r['input_id']: r['quantity'] for r in recs}}

    def get_raw_totals(item_id, qty, depth=0):
        if depth > 15:
            return {item_id: qty}
        com = commodities.get(item_id)
        if not com or not com['recipe']:
            return {item_id: qty}
        totals = {}
        for inp_id, inp_qty in com['recipe'].items():
            sub = get_raw_totals(inp_id, inp_qty * qty, depth + 1)
            for k, v in sub.items():
                totals[k] = totals.get(k, 0) + v
        return totals

    def calc_iron(table, id_col, bc_col, label):
        row = conn.execute(f"SELECT {bc_col} FROM {table} WHERE {id_col}=?", (label,)).fetchone()
        if not row:
            return
        bc = json.loads(row[bc_col])
        all_raws = {}
        for item_id, qty in bc.items():
            sub = get_raw_totals(item_id, qty)
            for k, v in sub.items():
                all_raws[k] = all_raws.get(k, 0) + v
        iron = all_raws.get('iron_ore', 0)
        total = sum(v for k, v in all_raws.items())
        return iron, total

    ships_to_check = [
        ('ship_types', 'id', 'build_cost', 'pinto_runner', 'Pinto Runner (T1 hauler)'),
        ('ship_types', 'id', 'build_cost', 'clydesdale', 'Clydesdale (T4 hauler)'),
        ('military_ships', 'id', 'build_cost', 'tf_interceptor', 'Aquila (fighter)'),
        ('military_ships', 'id', 'build_cost', 'tf_frigate', 'Centurion (frigate)'),
        ('military_ships', 'id', 'build_cost', 'tf_destroyer', 'Tribune (destroyer)'),
        ('military_ships', 'id', 'build_cost', 'tf_cruiser', 'Praetor (cruiser)'),
        ('military_ships', 'id', 'build_cost', 'tf_battlecruiser', 'Consul (battlecruiser)'),
        ('military_ships', 'id', 'build_cost', 'tf_battleship', 'Imperator (battleship)'),
        ('military_ships', 'id', 'build_cost', 'tf_dreadnought', 'Sovereign (dreadnought)'),
    ]

    print(f"{'Ship':<35} {'Iron Ore':>12} {'Total Raw':>12}")
    print("-" * 62)
    for table, id_col, bc_col, sid, name in ships_to_check:
        result = calc_iron(table, id_col, bc_col, sid)
        if result:
            iron, total = result
            print(f"{name:<35} {iron:>12,.0f} {total:>12,.0f}")

    conn.close()


if __name__ == "__main__":
    fix()
