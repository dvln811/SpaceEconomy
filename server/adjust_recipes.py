"""Adjust recipe multiplier from 5x to 3x (relative to original).
Current state: recipes are at 5x original. We want 3x original.
So divide all recipe quantities by 5, then multiply by 3 (i.e., multiply by 0.6).
"""
import sqlite3
import json
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")


def migrate():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Adjust recipes: current is 5x original, want 3x original -> multiply by 3/5
    recipes = conn.execute("SELECT commodity_id, input_id, quantity FROM recipes").fetchall()
    for r in recipes:
        new_qty = r['quantity'] * 3 / 5
        conn.execute("UPDATE recipes SET quantity=? WHERE commodity_id=? AND input_id=?",
                     (new_qty, r['commodity_id'], r['input_id']))
    print(f"Adjusted {len(recipes)} recipes from 5x to 3x (multiplied by 0.6)")

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

    def calc_ship(table, sid):
        row = conn.execute(f"SELECT build_cost FROM {table} WHERE id=?", (sid,)).fetchone()
        bc = json.loads(row['build_cost'])
        all_raws = {}
        for item_id, qty in bc.items():
            sub = get_raw_totals(item_id, qty)
            for k, v in sub.items():
                all_raws[k] = all_raws.get(k, 0) + v
        return all_raws.get('iron_ore', 0), sum(all_raws.values())

    # Check sample recipe
    ri = commodities.get('refined_iron', {}).get('recipe', {})
    print(f"Refined Iron recipe: {ri}")
    sp = commodities.get('steel_plate', {}).get('recipe', {})
    print(f"Steel Plate recipe: {sp}")

    print(f"\n{'Ship':<35} {'Iron Ore':>12} {'Total Raw':>12}")
    print("-" * 62)
    for sid, name, table in [
        ('pinto_runner', 'Pinto Runner', 'ship_types'),
        ('tf_interceptor', 'Aquila (fighter)', 'military_ships'),
        ('tf_frigate', 'Centurion (frigate)', 'military_ships'),
        ('tf_destroyer', 'Tribune (destroyer)', 'military_ships'),
        ('tf_cruiser', 'Praetor (cruiser)', 'military_ships'),
        ('tf_battlecruiser', 'Consul (battlecruiser)', 'military_ships'),
        ('tf_battleship', 'Imperator (battleship)', 'military_ships'),
        ('tf_dreadnought', 'Sovereign (dreadnought)', 'military_ships'),
    ]:
        iron, total = calc_ship(table, sid)
        print(f"{name:<35} {iron:>12,.0f} {total:>12,.0f}")

    conn.close()


if __name__ == "__main__":
    migrate()
