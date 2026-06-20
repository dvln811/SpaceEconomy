"""Economy rescaling: EVE-scale mineral requirements.

Changes:
1. Add hull_plating as T3 commodity (recipe: 3 steel_plate + 1 carbon_composite)
2. Multiply all recipe quantities by 5
3. Multiply all ship build_cost values by 10
"""
import sqlite3
import json
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

RECIPE_MULTIPLIER = 5
SHIP_BUILD_MULTIPLIER = 10


def migrate():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # 1. Add hull_plating as a T3 commodity if it doesn't exist
    exists = conn.execute("SELECT id FROM commodities WHERE id='hull_plating'").fetchone()
    if not exists:
        conn.execute("""INSERT INTO commodities (id, name, base_price, tier, volume, elasticity, description, category, subcategory, stats)
            VALUES ('hull_plating', 'Hull Plating', 500, 3, 0.2, 1.0,
            'Reinforced structural panels combining steel and carbon composite. The primary building material for all ship hulls.',
            'Manufactured', '', '{}')""")
        conn.execute("INSERT INTO recipes (commodity_id, input_id, quantity) VALUES ('hull_plating', 'steel_plate', 3)")
        conn.execute("INSERT INTO recipes (commodity_id, input_id, quantity) VALUES ('hull_plating', 'carbon_composite', 1)")
        print("Added hull_plating as T3 commodity (3 steel_plate + 1 carbon_composite)")
    else:
        print("hull_plating already exists, skipping creation")

    # 2. Multiply all recipe quantities by RECIPE_MULTIPLIER
    recipes = conn.execute("SELECT commodity_id, input_id, quantity FROM recipes").fetchall()
    for r in recipes:
        new_qty = r['quantity'] * RECIPE_MULTIPLIER
        conn.execute("UPDATE recipes SET quantity=? WHERE commodity_id=? AND input_id=?",
                     (new_qty, r['commodity_id'], r['input_id']))
    print(f"Scaled {len(recipes)} recipe entries by {RECIPE_MULTIPLIER}x")

    # 3. Multiply all ship build_cost values by SHIP_BUILD_MULTIPLIER
    # Military ships
    mil_ships = conn.execute("SELECT id, build_cost FROM military_ships").fetchall()
    for s in mil_ships:
        bc = json.loads(s['build_cost'])
        bc = {k: v * SHIP_BUILD_MULTIPLIER for k, v in bc.items()}
        conn.execute("UPDATE military_ships SET build_cost=? WHERE id=?", (json.dumps(bc), s['id']))
    print(f"Scaled {len(mil_ships)} military ship build costs by {SHIP_BUILD_MULTIPLIER}x")

    # Civilian ships
    civ_ships = conn.execute("SELECT id, build_cost FROM ship_types").fetchall()
    for s in civ_ships:
        bc = json.loads(s['build_cost'])
        bc = {k: v * SHIP_BUILD_MULTIPLIER for k, v in bc.items()}
        conn.execute("UPDATE ship_types SET build_cost=? WHERE id=?", (json.dumps(bc), s['id']))
    print(f"Scaled {len(civ_ships)} civilian ship build costs by {SHIP_BUILD_MULTIPLIER}x")

    conn.commit()

    # Verify: calculate total iron for a dreadnought
    print("\n=== VERIFICATION ===")
    conn.row_factory = sqlite3.Row
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

    # Dreadnought
    dread = conn.execute("SELECT build_cost FROM military_ships WHERE id='tf_dreadnought'").fetchone()
    bc = json.loads(dread['build_cost'])
    all_raws = {}
    for item_id, qty in bc.items():
        sub = get_raw_totals(item_id, qty)
        for k, v in sub.items():
            all_raws[k] = all_raws.get(k, 0) + v

    iron = all_raws.get('iron_ore', 0)
    copper = all_raws.get('copper_ore', 0)
    total_common = sum(v for k, v in all_raws.items() if commodities.get(k, {}).get('recipe') == {})
    print(f"Dreadnought (Sovereign) total raw materials:")
    print(f"  Iron Ore:   {iron:,.0f}")
    print(f"  Copper Ore: {copper:,.0f}")
    print(f"  Total raw:  {total_common:,.0f}")

    # Fighter
    fighter = conn.execute("SELECT build_cost FROM military_ships WHERE id='tf_interceptor'").fetchone()
    bc = json.loads(fighter['build_cost'])
    all_raws = {}
    for item_id, qty in bc.items():
        sub = get_raw_totals(item_id, qty)
        for k, v in sub.items():
            all_raws[k] = all_raws.get(k, 0) + v
    iron_f = all_raws.get('iron_ore', 0)
    print(f"\nFighter (Aquila) Iron Ore: {iron_f:,.0f}")

    # Civilian hauler
    hauler = conn.execute("SELECT build_cost FROM ship_types WHERE id='pinto_runner'").fetchone()
    bc = json.loads(hauler['build_cost'])
    all_raws = {}
    for item_id, qty in bc.items():
        sub = get_raw_totals(item_id, qty)
        for k, v in sub.items():
            all_raws[k] = all_raws.get(k, 0) + v
    iron_h = all_raws.get('iron_ore', 0)
    print(f"Pinto Runner Iron Ore: {iron_h:,.0f}")

    conn.close()
    print("\nDone! Economy rescaled.")


if __name__ == "__main__":
    migrate()
