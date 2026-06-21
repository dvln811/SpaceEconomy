"""Fix military ship weapons, modules, and build_cost to use valid item IDs.
Build cost = hull materials + fitted weapons + fitted modules."""
import sqlite3
import json
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

# Map old IDs to new valid IDs
WEAPON_MAP = {
    'autocannon': 'autocannon',
    'autocannon_m': 'autocannon_m',
    'autocannon_l': 'autocannon_l',
    'autocannon_c': 'autocannon_c',
    'artillery': 'artillery',
    'artillery_m': 'artillery_m',
    'artillery_l': 'artillery_l',
    'artillery_c': 'artillery_c',
    'blaster': 'blaster',
    'blaster_m': 'blaster_m',
    'blaster_l': 'blaster_l',
    'blaster_c': 'blaster_c',
    'railgun': 'railgun',
    'railgun_m': 'railgun_m',
    'railgun_l': 'railgun_l',
    'railgun_c': 'railgun_c',
    'pulse_laser': 'pulse_laser',
    'pulse_laser_m': 'pulse_laser_m',
    'pulse_laser_l': 'pulse_laser_l',
    'pulse_laser_c': 'pulse_laser_c',
    'beam_laser': 'beam_laser',
    'beam_laser_m': 'beam_laser_m',
    'beam_laser_l': 'beam_laser_l',
    'beam_laser_c': 'beam_laser_c',
    'missile_launcher': 'missile_launcher',
    'missile_launcher_m': 'missile_launcher_m',
    'missile_launcher_l': 'missile_launcher_l',
    'missile_launcher_c': 'missile_launcher_c',
    'torpedo_launcher': 'torpedo_launcher',
    'torpedo_launcher_m': 'torpedo_launcher_m',
    'torpedo_launcher_l': 'torpedo_launcher_l',
    'torpedo_launcher_c': 'torpedo_launcher_c',
    'rocket_launcher': 'rocket_launcher',
    'rocket_launcher_m': 'rocket_launcher_m',
    'rocket_launcher_l': 'rocket_launcher_l',
    'gauss_cannon': 'gauss_cannon',
    'gauss_cannon_m': 'gauss_cannon_m',
    'gauss_cannon_l': 'gauss_cannon_l',
    'gauss_cannon_c': 'gauss_cannon_c',
    'plasma_cannon': 'plasma_cannon',
    'plasma_cannon_m': 'plasma_cannon_m',
    'plasma_cannon_l': 'plasma_cannon_l',
    'plasma_cannon_c': 'plasma_cannon_c',
    'flak_battery': 'flak_battery',
    'flak_battery_m': 'flak_battery_m',
    'flak_battery_l': 'flak_battery_l',
    'point_defense': 'flak_battery',  # map to flak
    'combat_drone': 'combat_drone_kin',
    'ecm_jammer': 'ecm_jammer',
}

MODULE_MAP = {
    'shield_generator': 'shield_booster',
    'shield_gen_m': 'shield_booster_m',
    'shield_gen_l': 'shield_booster_l',
    'armor_plates': 'armor_plate',
    'armor_plates_m': 'armor_plate_m',
    'armor_plates_l': 'armor_plate_l',
    'std_engine': 'afterburner',
    'jump_drive': 'afterburner_l',
    'repair_module': 'armor_repairer',
    'scanner_array': 'scanner',
    'maneuver_rig': 'inertial_stab',
    'afterburner': 'afterburner',
    'afterburner_m': 'afterburner_m',
    'afterburner_l': 'afterburner_l',
}

# Hull material costs by class (base materials to build the hull itself)
HULL_MATERIALS = {
    'fighter':       {'armor_compound': 5, 'propulsion_unit': 2, 'microprocessor': 3},
    'frigate':       {'armor_compound': 15, 'propulsion_unit': 5, 'microprocessor': 8, 'reactor_core': 1},
    'destroyer':     {'armor_compound': 40, 'propulsion_unit': 10, 'microprocessor': 15, 'reactor_core': 2},
    'cruiser':       {'armor_compound': 100, 'propulsion_unit': 20, 'microprocessor': 30, 'reactor_core': 5},
    'battlecruiser': {'armor_compound': 200, 'propulsion_unit': 35, 'microprocessor': 50, 'reactor_core': 10},
    'battleship':    {'armor_compound': 400, 'propulsion_unit': 60, 'microprocessor': 80, 'reactor_core': 20},
    'dreadnought':   {'armor_compound': 1000, 'propulsion_unit': 120, 'microprocessor': 150, 'reactor_core': 50, 'warp_coil': 10},
}

# Weapon size by hull class
WEAPON_SIZE = {
    'fighter': '',       # small
    'frigate': '',       # small
    'destroyer': '_m',   # medium
    'cruiser': '_m',     # medium
    'battlecruiser': '_l',  # large
    'battleship': '_l',     # large
    'dreadnought': '_c',    # capital
}

MODULE_SIZE = {
    'fighter': '',
    'frigate': '',
    'destroyer': '_m',
    'cruiser': '_m',
    'battlecruiser': '_l',
    'battleship': '_l',
    'dreadnought': '_c',
}


def fix_military_ships():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Load valid commodity IDs
    valid_ids = set(r[0] for r in conn.execute("SELECT id FROM commodities"))

    ships = conn.execute("SELECT * FROM military_ships").fetchall()

    for ship in ships:
        hull_class = ship['hull_class']
        weapons = json.loads(ship['weapons'])
        modules = json.loads(ship['modules'])
        size_suffix = WEAPON_SIZE.get(hull_class, '')
        mod_suffix = MODULE_SIZE.get(hull_class, '')

        # Fix weapon IDs - assign correct size based on hull class
        new_weapons = []
        for w in weapons:
            # Strip any existing size suffix to get base
            base = w.replace('_c', '').replace('_l', '').replace('_m', '')
            # Look up in map or construct with correct size
            sized_id = base + size_suffix
            if sized_id in valid_ids:
                new_weapons.append(sized_id)
            elif base in valid_ids:
                new_weapons.append(base)
            elif w in WEAPON_MAP and WEAPON_MAP[w] in valid_ids:
                new_weapons.append(WEAPON_MAP[w])
            else:
                # Try base + size
                for try_id in [base + size_suffix, base, WEAPON_MAP.get(w, w)]:
                    if try_id in valid_ids:
                        new_weapons.append(try_id)
                        break
                else:
                    new_weapons.append(w)  # keep as-is if can't resolve

        # Fix module IDs
        new_modules = []
        for m in modules:
            base = m.replace('_c', '').replace('_l', '').replace('_m', '')
            if m in MODULE_MAP:
                mapped = MODULE_MAP[m]
                # Apply size if the mapped doesn't already have one
                if mod_suffix and not mapped.endswith(('_m', '_l', '_c')):
                    sized = mapped + mod_suffix
                    new_modules.append(sized if sized in valid_ids else mapped)
                else:
                    new_modules.append(mapped)
            elif base + mod_suffix in valid_ids:
                new_modules.append(base + mod_suffix)
            elif m in valid_ids:
                new_modules.append(m)
            else:
                new_modules.append(m)

        # Build cost = hull materials + 1x each fitted weapon + 1x each fitted module
        build_cost = dict(HULL_MATERIALS.get(hull_class, {}))
        for w in new_weapons:
            build_cost[w] = build_cost.get(w, 0) + 1
        for m in new_modules:
            if m in valid_ids:
                build_cost[m] = build_cost.get(m, 0) + 1

        # Update DB
        conn.execute(
            "UPDATE military_ships SET weapons=?, modules=?, build_cost=? WHERE id=?",
            (json.dumps(new_weapons), json.dumps(new_modules), json.dumps(build_cost), ship['id'])
        )

    conn.commit()

    # Verify
    ships = conn.execute("SELECT id, name, weapons, modules, build_cost FROM military_ships LIMIT 5").fetchall()
    for s in ships:
        w = json.loads(s['weapons'])
        bc = json.loads(s['build_cost'])
        invalid_w = [x for x in w if x not in valid_ids]
        invalid_bc = [x for x in bc if x not in valid_ids]
        if invalid_w or invalid_bc:
            print(f"  WARNING {s['name']}: invalid weapons={invalid_w} cost={invalid_bc}")
        else:
            print(f"  OK: {s['name']} - {len(w)} weapons, {len(bc)} cost items")

    # Full check
    all_ships = conn.execute("SELECT name, weapons, modules, build_cost FROM military_ships").fetchall()
    total_invalid = 0
    for s in all_ships:
        for field in ['weapons', 'modules', 'build_cost']:
            data = json.loads(s[field])
            items = data if isinstance(data, list) else data.keys()
            for item in items:
                if item not in valid_ids:
                    total_invalid += 1
    print(f"\nTotal invalid references: {total_invalid}")
    conn.close()


if __name__ == '__main__':
    fix_military_ships()
