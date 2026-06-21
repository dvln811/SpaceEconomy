"""Comprehensive data cleanup pass:
1. Fix display formatting in stats (title case quality, uppercase acronyms)
2. Full ammo descriptions
3. Weapon stats: remove DPS, add range_mod/rof_mod/tracking
4. Add hardpoints to military_ships (weapon_mounts/utility_bays/core_slots)
"""
import sqlite3, json, os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

# Ammo descriptions by weapon type and variant
AMMO_DESC = {
    'autocannon': {
        'standard': 'Electromagnetic round that disrupts shield systems. Balanced damage and range.',
        'barrage': 'Extended-range kinetic round with reduced tracking. Ideal for kiting engagements.',
        'hail': 'High-explosive close-range round. Maximum damage at the cost of optimal range.',
    },
    'artillery': {
        'standard': 'Depleted uranium shell with high mass. Devastating alpha strikes at long range.',
        'tremor': 'Long-range explosive shell. Extreme reach but poor tracking against small targets.',
        'quake': 'Short-range kinetic shell with massive impact. Shatters armor plating.',
    },
    'blaster': {
        'antimatter': 'Dense antimatter charge. Highest damage hybrid ammo at close range.',
        'void': 'Superheated plasma charge. Extreme thermal damage with tracking penalty.',
        'null': 'Optimized long-range hybrid charge. Extended falloff at reduced damage.',
    },
    'railgun': {
        'tungsten': 'High-density tungsten slug. Balanced range and damage for railgun platforms.',
        'javelin': 'Short-range high-velocity slug. Sacrifices range for devastating impact.',
        'spike': 'Ultra-long-range penetrator. Maximum range at reduced damage output.',
    },
    'pulse_laser': {
        'multifreq': 'Multi-frequency crystal. Maximum EM damage at reduced optimal range.',
        'conflag': 'Conflagration crystal. Extreme thermal damage with severe tracking penalty.',
        'scorch': 'Extended-range crystal. Doubles optimal range at moderate damage reduction.',
    },
    'beam_laser': {
        'microwave': 'Standard microwave crystal. Balanced EM damage across all ranges.',
        'aurora': 'Extreme-range crystal. Pushes beam weapons to maximum distance.',
        'gleam': 'Short-range thermal crystal. Massive damage within close optimal.',
    },
    'rocket_launcher': {
        'inferno': 'Thermal warhead rocket. Fast flight time, effective against shield-tanked targets.',
        'nova': 'Explosive warhead rocket. High area damage, effective against armor.',
        'mjolnir': 'Electromagnetic warhead. Disrupts electronics and shield systems on impact.',
    },
    'missile_launcher': {
        'inferno': 'Thermal warhead missile. Sustained damage over long range engagements.',
        'scourge': 'Kinetic warhead missile. Punches through armor with raw impact force.',
        'fury': 'Heavy explosive warhead. Maximum damage at the cost of flight speed.',
    },
    'torpedo_launcher': {
        'inferno': 'Heavy thermal torpedo. Designed for capital ship engagements.',
        'mjolnir': 'EM disruption torpedo. Overloads target capacitor and shield systems.',
        'rage': 'Maximum yield explosive torpedo. Devastating against structures and capitals.',
    },
    'gauss_cannon': {
        'standard': 'Magnetically accelerated slug. Penetrates shields with EM disruption.',
        'penetrator': 'Armor-piercing slug. Bypasses shield resistances to damage hull directly.',
    },
    'plasma_cannon': {
        'standard': 'Superheated plasma cell. Reliable thermal damage at medium range.',
        'overcharged': 'Overloaded plasma cell. Higher damage with increased heat generation.',
    },
    'flak_battery': {
        'shrapnel': 'Fragmenting shell. Effective against drones and fighter squadrons.',
        'proximity': 'Proximity-fused shell. Detonates near target for area denial.',
    },
}

# Hardpoints by hull class
HARDPOINTS = {
    'fighter':       {'weapon_mounts': 2, 'utility_bays': 1, 'core_slots': 1},
    'frigate':       {'weapon_mounts': 3, 'utility_bays': 2, 'core_slots': 2},
    'destroyer':     {'weapon_mounts': 4, 'utility_bays': 3, 'core_slots': 2},
    'cruiser':       {'weapon_mounts': 5, 'utility_bays': 4, 'core_slots': 3},
    'battlecruiser': {'weapon_mounts': 6, 'utility_bays': 5, 'core_slots': 4},
    'battleship':    {'weapon_mounts': 7, 'utility_bays': 5, 'core_slots': 5},
    'carrier':       {'weapon_mounts': 4, 'utility_bays': 7, 'core_slots': 6},
    'dreadnought':   {'weapon_mounts': 8, 'utility_bays': 6, 'core_slots': 5},
}


def run():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # ── 1. Fix stats formatting ──
    print("1. Fixing stats formatting...")
    items = conn.execute("SELECT id, stats FROM commodities WHERE stats != '' AND stats != '{}'").fetchall()
    fixed = 0
    for item in items:
        stats = json.loads(item['stats'])
        changed = False

        # Title case quality
        if 'quality' in stats and stats['quality'] != stats['quality'].title():
            stats['quality'] = stats['quality'].title()
            changed = True

        # Uppercase damage_type acronyms
        if 'damage_type' in stats:
            dt = stats['damage_type']
            if dt == 'em':
                stats['damage_type'] = 'EM'
                changed = True
            elif dt in ('kinetic', 'thermal', 'explosive'):
                stats['damage_type'] = dt.title()
                changed = True

        # Uppercase size
        if 'size' in stats and len(stats['size']) == 1 and stats['size'].islower():
            stats['size'] = stats['size'].upper()
            changed = True

        if changed:
            conn.execute("UPDATE commodities SET stats=? WHERE id=?", (json.dumps(stats), item['id']))
            fixed += 1
    print(f"   Fixed {fixed} items")

    # ── 2. Ammo descriptions ──
    print("2. Writing ammo descriptions...")
    ammo_items = conn.execute("SELECT id, stats FROM commodities WHERE category='Ammunition'").fetchall()
    desc_count = 0
    for item in ammo_items:
        stats = json.loads(item['stats'])
        weapon = stats.get('for_weapon', '')
        # Extract variant from ID: ammo_{weapon}_{variant}_{size}[_{quality}]
        parts = item['id'].split('_')
        # Find variant: it's after the weapon name parts
        variant = ''
        if weapon in AMMO_DESC:
            # Try to match variant
            for v in AMMO_DESC[weapon]:
                if v in item['id']:
                    variant = v
                    break

        if weapon in AMMO_DESC and variant in AMMO_DESC[weapon]:
            desc = AMMO_DESC[weapon][variant]
            quality = stats.get('quality', 'Standard')
            if quality == 'Faction':
                desc = "Navy-issue. " + desc + " Enhanced damage output."
            elif quality == 'T2':
                desc = "Advanced manufacture. " + desc + " Requires specialized launchers."
            conn.execute("UPDATE commodities SET description=? WHERE id=?", (desc, item['id']))
            desc_count += 1
    print(f"   Updated {desc_count} ammo descriptions")

    # ── 3. Fix weapon stats: weapons modify range/RoF/tracking, not damage ──
    print("3. Fixing weapon stats model...")
    weapons = conn.execute("SELECT id, stats FROM commodities WHERE category='Weapons'").fetchall()
    wep_fixed = 0
    for item in weapons:
        stats = json.loads(item['stats'])
        changed = False

        # Remove DPS (damage comes from ammo)
        if 'dps' in stats:
            del stats['dps']
            changed = True

        # Add weapon modifier stats if missing
        size_mult = {'S': 1.0, 'M': 1.5, 'L': 2.0, 'C': 3.0}.get(stats.get('size', 'S'), 1.0)
        qual_mult = {'Standard': 1.0, 'Named': 1.1, 'T2': 1.25, 'Faction': 1.2}.get(stats.get('quality', 'Standard'), 1.0)

        if 'rof_bonus' not in stats:
            # Rate of fire bonus percentage
            stats['rof_bonus'] = round(5 * qual_mult, 1)
            changed = True
        if 'tracking' not in stats:
            # Tracking speed (smaller weapons track faster)
            base_tracking = {'S': 80, 'M': 50, 'L': 25, 'C': 10}.get(stats.get('size', 'S'), 50)
            stats['tracking'] = round(base_tracking * qual_mult)
            changed = True
        if 'optimal_range' not in stats:
            stats['optimal_range'] = stats.pop('range', 5000)
            changed = True
        elif 'range' in stats:
            del stats['range']
            changed = True

        # Set slot type
        if 'slot' not in stats:
            stats['slot'] = 'weapon_mount'
            changed = True

        if changed:
            conn.execute("UPDATE commodities SET stats=? WHERE id=?", (json.dumps(stats), item['id']))
            wep_fixed += 1
    print(f"   Fixed {wep_fixed} weapon stats")

    # ── 4. Add hardpoints to military_ships ──
    print("4. Adding hardpoints to military ships...")
    cols = [r[1] for r in conn.execute('PRAGMA table_info(military_ships)')]
    if 'hardpoints' not in cols:
        conn.execute("ALTER TABLE military_ships ADD COLUMN hardpoints TEXT DEFAULT '{}'")
        conn.commit()

    ships = conn.execute("SELECT id, hull_class FROM military_ships").fetchall()
    for ship in ships:
        hp = HARDPOINTS.get(ship['hull_class'], {'weapon_mounts': 3, 'utility_bays': 2, 'core_slots': 2})
        conn.execute("UPDATE military_ships SET hardpoints=? WHERE id=?", (json.dumps(hp), ship['id']))
    print(f"   Set hardpoints for {len(ships)} ships")

    # ── Also fix module slot names to match new terminology ──
    print("5. Updating module slot names...")
    slot_map = {'high': 'weapon_mount', 'mid': 'utility_bay', 'low': 'core_slot'}
    modules = conn.execute("SELECT id, stats FROM commodities WHERE category='Ship Equipment'").fetchall()
    slot_fixed = 0
    for item in modules:
        stats = json.loads(item['stats'])
        if 'slot' in stats and stats['slot'] in slot_map:
            stats['slot'] = slot_map[stats['slot']]
            conn.execute("UPDATE commodities SET stats=? WHERE id=?", (json.dumps(stats), item['id']))
            slot_fixed += 1
    print(f"   Fixed {slot_fixed} module slot names")

    conn.commit()
    conn.close()
    print("\nDone!")


if __name__ == '__main__':
    run()
