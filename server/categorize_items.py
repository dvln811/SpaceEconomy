"""Add proper hierarchical categorization to all items.
Schema: category > subcategory > group
Stored as columns on the commodities table."""
import sqlite3
import json
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")


def categorize():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Add columns if not exist
    cols = [r[1] for r in conn.execute('PRAGMA table_info(commodities)')]
    if 'subcategory' not in cols:
        conn.execute("ALTER TABLE commodities ADD COLUMN subcategory TEXT DEFAULT ''")
    if 'group_name' not in cols:
        conn.execute("ALTER TABLE commodities ADD COLUMN group_name TEXT DEFAULT ''")
    conn.commit()

    # Load all items
    rows = conn.execute("SELECT id, name, category, stats FROM commodities").fetchall()

    for row in rows:
        item_id = row['id']
        stats = json.loads(row['stats']) if row['stats'] else {}
        current_cat = row['category'] or ''
        name = row['name']

        cat, subcat, group = classify(item_id, name, current_cat, stats)

        conn.execute(
            "UPDATE commodities SET category=?, subcategory=?, group_name=? WHERE id=?",
            (cat, subcat, group, item_id)
        )

    conn.commit()

    # Report
    rows = conn.execute("""
        SELECT category, subcategory, group_name, COUNT(*) as cnt 
        FROM commodities GROUP BY category, subcategory, group_name 
        ORDER BY category, subcategory, group_name
    """).fetchall()
    print("Hierarchy:")
    last_cat = ''
    last_sub = ''
    for r in rows:
        if r['category'] != last_cat:
            print(f"\n{r['category']}")
            last_cat = r['category']
            last_sub = ''
        if r['subcategory'] != last_sub:
            print(f"  {r['subcategory']}")
            last_sub = r['subcategory']
        print(f"    {r['group_name']}: {r['cnt']}")

    total = conn.execute("SELECT COUNT(*) FROM commodities").fetchone()[0]
    print(f"\nTotal: {total}")
    conn.close()


def classify(item_id, name, current_cat, stats):
    """Determine category > subcategory > group for an item."""
    weapon_class = stats.get('weapon_class', '')
    size = stats.get('size', '')
    quality = stats.get('quality', '')
    damage_type = stats.get('damage_type', '')
    for_weapon = stats.get('for_weapon', '')

    # ── Weapons ──
    if current_cat == 'Weapons' or weapon_class:
        # Determine subcategory by weapon class
        if weapon_class == 'Projectile':
            subcat = 'Turrets'
            if 'autocannon' in item_id:
                group = 'Autocannon'
            elif 'artillery' in item_id:
                group = 'Artillery'
            elif 'flak' in item_id:
                group = 'Flak Battery'
            else:
                group = 'Projectile'
        elif weapon_class == 'Hybrid':
            subcat = 'Turrets'
            if 'blaster' in item_id:
                group = 'Blaster'
            elif 'railgun' in item_id:
                group = 'Railgun'
            else:
                group = 'Hybrid'
        elif weapon_class == 'Energy':
            subcat = 'Energy Weapons'
            if 'pulse' in item_id:
                group = 'Pulse Laser'
            elif 'beam' in item_id:
                group = 'Beam Laser'
            elif 'plasma' in item_id:
                group = 'Plasma Cannon'
            else:
                group = 'Energy'
        elif weapon_class == 'Missile':
            subcat = 'Launchers'
            if 'rocket' in item_id:
                group = 'Rocket Launcher'
            elif 'torpedo' in item_id:
                group = 'Torpedo Launcher'
            elif 'missile' in item_id:
                group = 'Missile Launcher'
            else:
                group = 'Launcher'
        elif weapon_class == 'Magnetic':
            subcat = 'Turrets'
            group = 'Gauss Cannon'
        else:
            subcat = 'Other'
            group = weapon_class or 'Unknown'
        return 'Weapons', subcat, group

    # ── Ammunition ──
    if current_cat == 'Ammunition' or for_weapon or item_id.startswith('ammo_'):
        # Determine group by what weapon it's for
        if 'autocannon' in item_id or for_weapon == 'autocannon':
            return 'Ammunition', 'Projectile Ammo', 'Autocannon Rounds'
        elif 'artillery' in item_id or for_weapon == 'artillery':
            return 'Ammunition', 'Projectile Ammo', 'Artillery Shells'
        elif 'blaster' in item_id or for_weapon == 'blaster':
            return 'Ammunition', 'Hybrid Charges', 'Blaster Charges'
        elif 'railgun' in item_id or for_weapon == 'railgun':
            return 'Ammunition', 'Hybrid Charges', 'Railgun Charges'
        elif 'pulse' in item_id or for_weapon == 'pulse_laser':
            return 'Ammunition', 'Energy Crystals', 'Pulse Crystals'
        elif 'beam' in item_id or for_weapon == 'beam_laser':
            return 'Ammunition', 'Energy Crystals', 'Beam Crystals'
        elif 'rocket' in item_id or for_weapon == 'rocket_launcher':
            return 'Ammunition', 'Missiles', 'Rockets'
        elif 'missile' in item_id or for_weapon == 'missile_launcher':
            return 'Ammunition', 'Missiles', 'Missiles'
        elif 'torpedo' in item_id or for_weapon == 'torpedo_launcher':
            return 'Ammunition', 'Missiles', 'Torpedoes'
        elif 'gauss' in item_id or for_weapon == 'gauss_cannon':
            return 'Ammunition', 'Magnetic Ammo', 'Gauss Slugs'
        elif 'plasma' in item_id or for_weapon == 'plasma_cannon':
            return 'Ammunition', 'Energy Cells', 'Plasma Cells'
        elif 'flak' in item_id or for_weapon == 'flak_battery':
            return 'Ammunition', 'Projectile Ammo', 'Flak Shells'
        return 'Ammunition', 'General', 'Rounds'

    # ── Defense ──
    if current_cat == 'Defense':
        if 'shield_booster' in item_id:
            return 'Ship Equipment', 'Shields', 'Shield Boosters'
        elif 'shield_hardener' in item_id:
            return 'Ship Equipment', 'Shields', 'Shield Hardeners'
        elif 'shield_extender' in item_id:
            return 'Ship Equipment', 'Shields', 'Shield Extenders'
        elif 'shield_recharger' in item_id:
            return 'Ship Equipment', 'Shields', 'Shield Rechargers'
        elif 'armor_repairer' in item_id:
            return 'Ship Equipment', 'Armor', 'Armor Repairers'
        elif 'armor_hardener' in item_id:
            return 'Ship Equipment', 'Armor', 'Armor Hardeners'
        elif 'armor_plate' in item_id:
            return 'Ship Equipment', 'Armor', 'Armor Plates'
        elif 'damage_control' in item_id:
            return 'Ship Equipment', 'Hull', 'Damage Control'
        return 'Ship Equipment', 'Defense', 'General'

    # ── Propulsion ──
    if current_cat == 'Propulsion':
        if 'afterburner' in item_id:
            return 'Ship Equipment', 'Propulsion', 'Afterburners'
        elif 'mwd' in item_id:
            return 'Ship Equipment', 'Propulsion', 'Microwarpdrives'
        elif 'inertial' in item_id:
            return 'Ship Equipment', 'Navigation', 'Inertial Stabilizers'
        elif 'warp_core' in item_id:
            return 'Ship Equipment', 'Navigation', 'Warp Stabilizers'
        elif 'overdrive' in item_id:
            return 'Ship Equipment', 'Propulsion', 'Overdrive Injectors'
        elif 'nanofiber' in item_id:
            return 'Ship Equipment', 'Navigation', 'Nanofiber Structures'
        return 'Ship Equipment', 'Propulsion', 'General'

    # ── Electronic Warfare ──
    if current_cat == 'Electronic Warfare':
        if 'ecm' in item_id:
            return 'Ship Equipment', 'Electronic Warfare', 'ECM'
        elif 'sensor_damp' in item_id:
            return 'Ship Equipment', 'Electronic Warfare', 'Sensor Dampeners'
        elif 'target_painter' in item_id:
            return 'Ship Equipment', 'Electronic Warfare', 'Target Painters'
        elif 'tracking_disruptor' in item_id:
            return 'Ship Equipment', 'Electronic Warfare', 'Tracking Disruptors'
        elif 'warp_scrambler' in item_id:
            return 'Ship Equipment', 'Tackle', 'Warp Scramblers'
        elif 'warp_disruptor' in item_id:
            return 'Ship Equipment', 'Tackle', 'Warp Disruptors'
        elif 'stasis_web' in item_id:
            return 'Ship Equipment', 'Tackle', 'Stasis Webifiers'
        elif 'energy_neutralizer' in item_id:
            return 'Ship Equipment', 'Energy Warfare', 'Energy Neutralizers'
        elif 'energy_vampire' in item_id or 'nosferatu' in item_id:
            return 'Ship Equipment', 'Energy Warfare', 'Energy Nosferatu'
        elif 'remote_repper_armor' in item_id:
            return 'Ship Equipment', 'Remote Repair', 'Remote Armor Repairers'
        elif 'remote_repper_shield' in item_id:
            return 'Ship Equipment', 'Remote Repair', 'Remote Shield Boosters'
        return 'Ship Equipment', 'Electronic Warfare', 'General'

    # ── Engineering ──
    if current_cat == 'Engineering':
        if 'capacitor_battery' in item_id or 'cap_battery' in item_id:
            return 'Ship Equipment', 'Engineering', 'Capacitor Batteries'
        elif 'capacitor_booster' in item_id or 'cap_booster' in item_id:
            return 'Ship Equipment', 'Engineering', 'Capacitor Boosters'
        elif 'cap_recharger' in item_id:
            return 'Ship Equipment', 'Engineering', 'Capacitor Rechargers'
        elif 'power_diagnostic' in item_id:
            return 'Ship Equipment', 'Engineering', 'Power Diagnostics'
        elif 'reactor_control' in item_id:
            return 'Ship Equipment', 'Engineering', 'Reactor Controls'
        elif 'cpu_enhancer' in item_id or 'co_processor' in item_id:
            return 'Ship Equipment', 'Engineering', 'Co-Processors'
        elif 'cargo_expander' in item_id:
            return 'Ship Equipment', 'Hull', 'Cargo Expanders'
        elif 'drone_control' in item_id:
            return 'Ship Equipment', 'Drones', 'Drone Control Units'
        elif 'cloak' in item_id:
            return 'Ship Equipment', 'Electronics', 'Cloaking Devices'
        elif 'scanner' in item_id:
            return 'Ship Equipment', 'Electronics', 'Scanners'
        elif 'salvager' in item_id:
            return 'Ship Equipment', 'Electronics', 'Salvagers'
        elif 'tractor_beam' in item_id:
            return 'Ship Equipment', 'Electronics', 'Tractor Beams'
        return 'Ship Equipment', 'Engineering', 'General'

    # ── Drones ──
    if current_cat == 'Drones':
        if 'combat' in item_id:
            dtype = stats.get('damage_type', 'general')
            return 'Drones', 'Combat Drones', f'{dtype.title()} Drones'
        elif 'mining' in item_id:
            return 'Drones', 'Utility Drones', 'Mining Drones'
        elif 'salvage' in item_id:
            return 'Drones', 'Utility Drones', 'Salvage Drones'
        elif 'repair' in item_id:
            return 'Drones', 'Logistics Drones', 'Repair Drones'
        elif 'ewar' in item_id:
            return 'Drones', 'Electronic Warfare Drones', 'EWAR Drones'
        return 'Drones', 'General', 'Drones'

    # ── Mining ──
    if current_cat == 'Mining':
        if 'mining_laser' in item_id:
            return 'Ship Equipment', 'Mining', 'Mining Lasers'
        elif 'strip_miner' in item_id:
            return 'Ship Equipment', 'Mining', 'Strip Miners'
        elif 'ice_harvester' in item_id:
            return 'Ship Equipment', 'Mining', 'Ice Harvesters'
        elif 'gas_harvester' in item_id:
            return 'Ship Equipment', 'Mining', 'Gas Harvesters'
        elif 'mining_upgrade' in item_id:
            return 'Ship Equipment', 'Mining', 'Mining Upgrades'
        return 'Ship Equipment', 'Mining', 'General'

    # ── Materials ──
    if current_cat == 'Raw Materials':
        # Classify ores by type
        if 'ice' in item_id or 'nitrogen' in item_id or 'methane' in item_id or 'hydral' in item_id:
            return 'Materials', 'Raw Materials', 'Ice'
        elif 'crystal' in item_id or 'quartz' in item_id:
            return 'Materials', 'Raw Materials', 'Crystals'
        elif 'gas' in item_id or 'xenon' in item_id or 'helium' in item_id:
            return 'Materials', 'Raw Materials', 'Gas'
        elif 'bio' in item_id or 'spore' in item_id or 'amino' in item_id:
            return 'Materials', 'Raw Materials', 'Organic'
        elif 'void' in item_id or 'neutron' in item_id or 'krax' in item_id:
            return 'Materials', 'Raw Materials', 'Exotic'
        return 'Materials', 'Raw Materials', 'Ore'

    if current_cat == 'Refined Materials':
        return 'Materials', 'Refined Materials', 'Processed'

    if current_cat == 'Manufactured':
        return 'Materials', 'Manufactured', 'Advanced Materials'

    if current_cat == 'Components':
        return 'Materials', 'Components', 'Ship Components'

    if current_cat == 'Trade Goods':
        return 'Trade Goods', 'Commodities', 'Trade Goods'

    # Fallback
    return current_cat or 'Other', 'General', 'Uncategorized'


if __name__ == '__main__':
    categorize()
