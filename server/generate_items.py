"""Generate comprehensive item database (~1000+ items).
Sizes: Small, Medium, Large, Capital
Quality tiers: Standard, Named, T2, Faction
"""
import sqlite3
import json
import os
import math

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

# ── Size multipliers ──
SIZES = {
    'S': {'label': 'Small', 'price_mult': 1.0, 'stat_mult': 1.0, 'volume': 0.5},
    'M': {'label': 'Medium', 'price_mult': 3.0, 'stat_mult': 2.5, 'volume': 1.0},
    'L': {'label': 'Large', 'price_mult': 10.0, 'stat_mult': 6.0, 'volume': 2.0},
    'C': {'label': 'Capital', 'price_mult': 50.0, 'stat_mult': 20.0, 'volume': 5.0},
}

# ── Quality tiers ──
QUALITIES = {
    'standard': {'label': '', 'price_mult': 1.0, 'stat_mult': 1.0, 'tier_suffix': ''},
    'named': {'label': 'Compact', 'price_mult': 2.5, 'stat_mult': 1.15, 'tier_suffix': ' II'},
    't2': {'label': 'Advanced', 'price_mult': 8.0, 'stat_mult': 1.35, 'tier_suffix': ' T2'},
    'faction': {'label': 'Navy', 'price_mult': 15.0, 'stat_mult': 1.25, 'tier_suffix': ' Navy'},
}

# ── Weapon definitions ──
WEAPONS = [
    # (base_id, name, category, damage_type, base_price, base_dps, base_range, traits)
    ('autocannon', 'Autocannon', 'Projectile', 'kinetic', 2500, 45, 5000, 'Short range, high ROF'),
    ('artillery', 'Artillery Cannon', 'Projectile', 'explosive', 3000, 30, 25000, 'Long range, alpha strike'),
    ('blaster', 'Blaster', 'Hybrid', 'kinetic', 2800, 55, 3000, 'Highest DPS, shortest range'),
    ('railgun', 'Railgun', 'Hybrid', 'kinetic', 3500, 25, 35000, 'Extreme range, precision'),
    ('pulse_laser', 'Pulse Laser', 'Energy', 'em', 3000, 50, 8000, 'Good tracking, medium range'),
    ('beam_laser', 'Beam Laser', 'Energy', 'em', 3800, 28, 30000, 'Long range, consistent'),
    ('rocket_launcher', 'Rocket Launcher', 'Missile', 'explosive', 2200, 40, 10000, 'Fast missiles, short range'),
    ('missile_launcher', 'Missile Launcher', 'Missile', 'kinetic', 2800, 32, 45000, 'Long range, selectable damage'),
    ('torpedo_launcher', 'Torpedo Launcher', 'Missile', 'explosive', 4000, 60, 20000, 'Anti-capital, slow'),
    ('gauss_cannon', 'Gauss Cannon', 'Magnetic', 'em', 4500, 35, 20000, 'Penetrating, ignores shields'),
    ('plasma_cannon', 'Plasma Cannon', 'Energy', 'thermal', 3200, 48, 6000, 'High thermal damage'),
    ('flak_battery', 'Flak Battery', 'Projectile', 'explosive', 2000, 25, 8000, 'Anti-drone/fighter'),
]

# ── Defense modules ──
DEFENSE_SHIELDS = [
    ('shield_booster', 'Shield Booster', 4000, 80, 'Restores shield HP'),
    ('shield_hardener_em', 'EM Shield Hardener', 2000, 0, 'Resists EM damage'),
    ('shield_hardener_th', 'Thermal Shield Hardener', 2000, 0, 'Resists thermal damage'),
    ('shield_hardener_kin', 'Kinetic Shield Hardener', 2000, 0, 'Resists kinetic damage'),
    ('shield_hardener_exp', 'Explosive Shield Hardener', 2000, 0, 'Resists explosive damage'),
    ('shield_extender', 'Shield Extender', 3000, 100, 'Increases max shield HP'),
    ('shield_recharger', 'Shield Recharger', 1500, 0, 'Faster passive recharge'),
]

DEFENSE_ARMOR = [
    ('armor_repairer', 'Armor Repairer', 4500, 70, 'Restores armor HP'),
    ('armor_hardener_em', 'EM Armor Hardener', 2000, 0, 'Resists EM damage'),
    ('armor_hardener_th', 'Thermal Armor Hardener', 2000, 0, 'Resists thermal damage'),
    ('armor_hardener_kin', 'Kinetic Armor Hardener', 2000, 0, 'Resists kinetic damage'),
    ('armor_hardener_exp', 'Explosive Armor Hardener', 2000, 0, 'Resists explosive damage'),
    ('armor_plate', 'Armor Plate', 3500, 120, 'Increases max armor HP'),
    ('damage_control', 'Damage Control Unit', 5000, 0, 'Resists all damage types'),
]

# ── Propulsion ──
PROPULSION = [
    ('afterburner', 'Afterburner', 3000, 'Increases speed by 50%'),
    ('mwd', 'Microwarpdrive', 6000, 'Increases speed by 500%, sig bloom'),
    ('inertial_stab', 'Inertial Stabilizer', 2000, 'Reduces align time'),
    ('warp_core_stab', 'Warp Core Stabilizer', 1500, 'Resists warp scramble'),
    ('overdrive', 'Overdrive Injector', 2500, 'Passive speed bonus'),
    ('nanofiber', 'Nanofiber Structure', 2200, 'Speed + agility, less hull'),
]

# ── Utility/Electronic Warfare ──
EWAR = [
    ('ecm_jammer', 'ECM Jammer', 5000, 'Breaks target lock'),
    ('sensor_damp', 'Sensor Dampener', 4000, 'Reduces lock range/speed'),
    ('target_painter', 'Target Painter', 3500, 'Increases target signature'),
    ('tracking_disruptor', 'Tracking Disruptor', 3500, 'Reduces turret tracking'),
    ('warp_scrambler', 'Warp Scrambler', 4000, 'Prevents warp, short range'),
    ('warp_disruptor', 'Warp Disruptor', 3000, 'Prevents warp, long range'),
    ('stasis_web', 'Stasis Webifier', 4500, 'Reduces target speed 60%'),
    ('energy_neutralizer', 'Energy Neutralizer', 5500, 'Drains target capacitor'),
    ('energy_vampire', 'Energy Nosferatu', 4500, 'Drains cap, returns to self'),
    ('remote_repper_armor', 'Remote Armor Repairer', 5000, 'Repairs ally armor'),
    ('remote_repper_shield', 'Remote Shield Booster', 5000, 'Repairs ally shields'),
]

# ── Engineering ──
ENGINEERING = [
    ('capacitor_battery', 'Capacitor Battery', 2500, 'Increases cap capacity'),
    ('capacitor_booster', 'Capacitor Booster', 3000, 'Active cap injection'),
    ('cap_recharger', 'Capacitor Recharger', 1500, 'Faster cap recharge'),
    ('power_diagnostic', 'Power Diagnostic System', 2000, 'Bonus to PG/CPU/cap'),
    ('reactor_control', 'Reactor Control Unit', 2500, 'Increases powergrid'),
    ('cpu_enhancer', 'Co-Processor', 2000, 'Increases CPU'),
    ('cargo_expander', 'Cargo Expander', 1500, 'Increases cargo capacity'),
    ('drone_control', 'Drone Control Unit', 4000, 'Increases drone bandwidth'),
    ('cloak', 'Cloaking Device', 15000, 'Invisible while active'),
    ('scanner', 'Probe Scanner', 3000, 'Scans down signatures'),
    ('salvager', 'Salvager', 2500, 'Salvages wrecks'),
    ('tractor_beam', 'Tractor Beam', 3500, 'Pulls wrecks/cargo'),
]

# ── Drones ──
DRONES = [
    ('combat_drone_em', 'EM Combat Drone', 8000, 'em', 'Deals EM damage'),
    ('combat_drone_th', 'Thermal Combat Drone', 8000, 'thermal', 'Deals thermal damage'),
    ('combat_drone_kin', 'Kinetic Combat Drone', 8000, 'kinetic', 'Deals kinetic damage'),
    ('combat_drone_exp', 'Explosive Combat Drone', 8000, 'explosive', 'Deals explosive damage'),
    ('mining_drone', 'Mining Drone', 5000, 'none', 'Mines ore autonomously'),
    ('salvage_drone', 'Salvage Drone', 6000, 'none', 'Salvages wrecks autonomously'),
    ('repair_drone', 'Repair Drone', 10000, 'none', 'Repairs friendly ships'),
    ('ewar_drone', 'Electronic Warfare Drone', 9000, 'none', 'Applies EWAR effects'),
]

# ── Ammunition (per weapon system) ──
AMMO_TYPES = {
    'autocannon': [
        ('standard', 'EMP Round', 'em'),
        ('barrage', 'Barrage Round', 'kinetic'),
        ('hail', 'Hail Round', 'explosive'),
    ],
    'artillery': [
        ('standard', 'Depleted Uranium', 'kinetic'),
        ('tremor', 'Tremor Shell', 'explosive'),
        ('quake', 'Quake Shell', 'kinetic'),
    ],
    'blaster': [
        ('antimatter', 'Antimatter Charge', 'kinetic'),
        ('void', 'Void Charge', 'thermal'),
        ('null', 'Null Charge', 'kinetic'),
    ],
    'railgun': [
        ('tungsten', 'Tungsten Charge', 'kinetic'),
        ('javelin', 'Javelin Charge', 'kinetic'),
        ('spike', 'Spike Charge', 'kinetic'),
    ],
    'pulse_laser': [
        ('multifreq', 'Multifrequency Crystal', 'em'),
        ('conflag', 'Conflagration Crystal', 'thermal'),
        ('scorch', 'Scorch Crystal', 'em'),
    ],
    'beam_laser': [
        ('microwave', 'Microwave Crystal', 'em'),
        ('aurora', 'Aurora Crystal', 'em'),
        ('gleam', 'Gleam Crystal', 'thermal'),
    ],
    'rocket_launcher': [
        ('inferno', 'Inferno Rocket', 'thermal'),
        ('nova', 'Nova Rocket', 'explosive'),
        ('mjolnir', 'Mjolnir Rocket', 'em'),
    ],
    'missile_launcher': [
        ('inferno', 'Inferno Missile', 'thermal'),
        ('scourge', 'Scourge Missile', 'kinetic'),
        ('fury', 'Fury Missile', 'explosive'),
    ],
    'torpedo_launcher': [
        ('inferno', 'Inferno Torpedo', 'thermal'),
        ('mjolnir', 'Mjolnir Torpedo', 'em'),
        ('rage', 'Rage Torpedo', 'explosive'),
    ],
    'gauss_cannon': [
        ('standard', 'Gauss Slug', 'em'),
        ('penetrator', 'Penetrator Slug', 'kinetic'),
    ],
    'plasma_cannon': [
        ('standard', 'Plasma Cell', 'thermal'),
        ('overcharged', 'Overcharged Cell', 'thermal'),
    ],
    'flak_battery': [
        ('shrapnel', 'Shrapnel Shell', 'explosive'),
        ('proximity', 'Proximity Shell', 'kinetic'),
    ],
}

# ── Mining equipment ──
MINING = [
    ('mining_laser', 'Mining Laser', 4000, 'Extracts ore from asteroids'),
    ('strip_miner', 'Strip Miner', 12000, 'High-yield mining (Large only)'),
    ('ice_harvester', 'Ice Harvester', 8000, 'Harvests ice deposits'),
    ('gas_harvester', 'Gas Cloud Harvester', 7000, 'Harvests gas clouds'),
    ('mining_upgrade', 'Mining Laser Upgrade', 3000, 'Increases mining yield'),
]

# ── T3 manufactured materials (inputs for T4 components) ──
T3_ADDITIONS = [
    ('synthetic_fiber', 'Synthetic Fiber', 800, 'Lightweight structural material'),
    ('photon_crystal', 'Photon Crystal', 1200, 'Energy weapon focusing element'),
    ('magnetic_coil', 'Magnetic Coil', 900, 'Electromagnetic propulsion component'),
    ('thermal_shielding', 'Thermal Shielding', 1000, 'Heat-resistant composite'),
    ('nanopaste', 'Nanopaste', 1500, 'Self-repairing material'),
]

# ── T4 component additions ──
T4_ADDITIONS = [
    ('weapon_core', 'Weapon Power Core', 5000, 'Powers weapon systems'),
    ('targeting_array', 'Targeting Array', 4500, 'Precision targeting computer'),
    ('propulsion_unit', 'Propulsion Unit', 4000, 'Thruster assembly'),
    ('shield_emitter', 'Shield Emitter', 4500, 'Projects energy shields'),
    ('armor_compound', 'Armor Compound', 3500, 'Reinforced hull material'),
    ('drone_cpu', 'Drone Control CPU', 6000, 'Autonomous drone brain'),
    ('cap_cell', 'Capacitor Cell', 3000, 'Energy storage unit'),
    ('sensor_cluster', 'Sensor Cluster', 5500, 'Multi-spectrum sensor'),
    ('warp_coil', 'Warp Field Coil', 8000, 'FTL drive component'),
    ('reactor_core', 'Reactor Core', 12000, 'Ship power plant'),
]


def generate_item_id(base, size, quality):
    """Generate a unique item ID."""
    parts = [base]
    if size != 'S':
        parts.append(size.lower())
    if quality != 'standard':
        parts.append(quality)
    return '_'.join(parts)


def generate_item_name(base_name, size, quality):
    """Generate display name."""
    size_label = SIZES[size]['label']
    q = QUALITIES[quality]
    if quality == 'standard':
        return f"{base_name} ({size_label})"
    elif quality == 'named':
        return f"{base_name} Compact ({size_label})"
    elif quality == 't2':
        return f"{base_name} II ({size_label})"
    elif quality == 'faction':
        return f"Navy {base_name} ({size_label})"
    return base_name


def calc_price(base_price, size, quality):
    return round(base_price * SIZES[size]['price_mult'] * QUALITIES[quality]['price_mult'], 0)


def calc_stat(base_val, size, quality):
    return round(base_val * SIZES[size]['stat_mult'] * QUALITIES[quality]['stat_mult'], 1)



def generate_all():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Preserve existing materials (T0-T2 ores, refined, trade goods)
    existing_ids = set(r[0] for r in conn.execute("SELECT id FROM commodities WHERE tier <= 2").fetchall())
    # Also preserve T3 manufactured and T4 components that recipes depend on
    existing_ids.update(r[0] for r in conn.execute("SELECT id FROM commodities WHERE tier IN (3,4)").fetchall())

    # Delete only T5 products (weapons, modules, etc.) - we'll regenerate them
    conn.execute("DELETE FROM commodities WHERE tier = 5")
    conn.execute("DELETE FROM recipes WHERE commodity_id NOT IN (SELECT id FROM commodities)")
    conn.commit()

    items = []  # (id, name, base_price, tier, volume, elasticity, description, category, stats)
    recipes = []  # (commodity_id, input_id, quantity)

    # ── Add new T3 materials ──
    for mid, name, price, desc in T3_ADDITIONS:
        if mid not in existing_ids:
            items.append((mid, name, price, 3, 0.5, 1.0, desc, 'Manufactured', {}))
            recipes.append((mid, 'refined_titanium', 2))
            recipes.append((mid, 'refined_copper', 1))

    # ── Add new T4 components ──
    for cid, name, price, desc in T4_ADDITIONS:
        if cid not in existing_ids:
            items.append((cid, name, price, 4, 1.0, 1.0, desc, 'Components', {}))
            recipes.append((cid, 'microprocessor', 2))
            recipes.append((cid, 'synthetic_polymer', 1))

    # ── Weapons ──
    t4_weapon_inputs = ['weapon_core', 'targeting_array']
    for base_id, name, cat, dmg_type, base_price, base_dps, base_range, traits in WEAPONS:
        for size_key, size_data in SIZES.items():
            for qual_key, qual_data in QUALITIES.items():
                item_id = generate_item_id(base_id, size_key, qual_key)
                item_name = generate_item_name(name, size_key, qual_key)
                price = calc_price(base_price, size_key, qual_key)
                dps = calc_stat(base_dps, size_key, qual_key)
                rng = calc_stat(base_range, size_key, qual_key)
                volume = size_data['volume']
                stats = {
                    'dps': dps, 'range': rng, 'damage_type': dmg_type,
                    'size': size_key, 'quality': qual_key, 'weapon_class': cat,
                }
                items.append((item_id, item_name, price, 5, volume, 1.2, traits, 'Weapons', stats))
                # Recipes scale with size and quality
                base_qty = size_data['price_mult']
                if qual_key == 'standard':
                    recipes.append((item_id, 'weapon_core', max(1, base_qty)))
                    recipes.append((item_id, 'microprocessor', max(1, base_qty * 0.5)))
                elif qual_key == 'named':
                    recipes.append((item_id, 'weapon_core', max(1, base_qty * 1.5)))
                    recipes.append((item_id, 'targeting_array', max(1, base_qty * 0.5)))
                elif qual_key == 't2':
                    recipes.append((item_id, 'weapon_core', max(1, base_qty * 2)))
                    recipes.append((item_id, 'targeting_array', max(1, base_qty)))
                    recipes.append((item_id, 'nanopaste', max(1, base_qty * 0.5)))
                elif qual_key == 'faction':
                    recipes.append((item_id, 'weapon_core', max(1, base_qty * 2.5)))
                    recipes.append((item_id, 'targeting_array', max(1, base_qty * 1.5)))
                    recipes.append((item_id, 'photon_crystal', max(1, base_qty)))

    # ── Defense (Shields) ──
    for base_id, name, base_price, base_hp, desc in DEFENSE_SHIELDS:
        for size_key, size_data in SIZES.items():
            for qual_key, qual_data in QUALITIES.items():
                item_id = generate_item_id(base_id, size_key, qual_key)
                item_name = generate_item_name(name, size_key, qual_key)
                price = calc_price(base_price, size_key, qual_key)
                hp = calc_stat(base_hp, size_key, qual_key) if base_hp else 0
                stats = {'hp_bonus': hp, 'size': size_key, 'quality': qual_key, 'slot': 'mid'}
                items.append((item_id, item_name, price, 5, size_data['volume'], 1.0, desc, 'Defense', stats))
                base_qty = size_data['price_mult']
                recipes.append((item_id, 'shield_emitter', max(1, base_qty)))
                recipes.append((item_id, 'microprocessor', max(1, base_qty * 0.5)))
                if qual_key in ('t2', 'faction'):
                    recipes.append((item_id, 'nanopaste', max(1, base_qty * 0.5)))

    # ── Defense (Armor) ──
    for base_id, name, base_price, base_hp, desc in DEFENSE_ARMOR:
        for size_key, size_data in SIZES.items():
            for qual_key, qual_data in QUALITIES.items():
                item_id = generate_item_id(base_id, size_key, qual_key)
                item_name = generate_item_name(name, size_key, qual_key)
                price = calc_price(base_price, size_key, qual_key)
                hp = calc_stat(base_hp, size_key, qual_key) if base_hp else 0
                stats = {'hp_bonus': hp, 'size': size_key, 'quality': qual_key, 'slot': 'low'}
                items.append((item_id, item_name, price, 5, size_data['volume'], 1.0, desc, 'Defense', stats))
                base_qty = size_data['price_mult']
                recipes.append((item_id, 'armor_compound', max(1, base_qty)))
                recipes.append((item_id, 'synthetic_polymer', max(1, base_qty * 0.5)))
                if qual_key in ('t2', 'faction'):
                    recipes.append((item_id, 'thermal_shielding', max(1, base_qty * 0.5)))

    # ── Propulsion ──
    for base_id, name, base_price, desc in PROPULSION:
        for size_key, size_data in SIZES.items():
            for qual_key, qual_data in QUALITIES.items():
                item_id = generate_item_id(base_id, size_key, qual_key)
                item_name = generate_item_name(name, size_key, qual_key)
                price = calc_price(base_price, size_key, qual_key)
                stats = {'size': size_key, 'quality': qual_key, 'slot': 'mid'}
                items.append((item_id, item_name, price, 5, size_data['volume'], 1.0, desc, 'Propulsion', stats))
                base_qty = size_data['price_mult']
                recipes.append((item_id, 'propulsion_unit', max(1, base_qty)))
                recipes.append((item_id, 'cap_cell', max(1, base_qty * 0.3)))
                if qual_key in ('t2', 'faction'):
                    recipes.append((item_id, 'magnetic_coil', max(1, base_qty * 0.5)))

    # ── EWAR ──
    for base_id, name, base_price, desc in EWAR:
        for size_key, size_data in SIZES.items():
            for qual_key, qual_data in QUALITIES.items():
                item_id = generate_item_id(base_id, size_key, qual_key)
                item_name = generate_item_name(name, size_key, qual_key)
                price = calc_price(base_price, size_key, qual_key)
                stats = {'size': size_key, 'quality': qual_key, 'slot': 'mid'}
                items.append((item_id, item_name, price, 5, size_data['volume'], 1.0, desc, 'Electronic Warfare', stats))
                base_qty = size_data['price_mult']
                recipes.append((item_id, 'sensor_cluster', max(1, base_qty)))
                recipes.append((item_id, 'microprocessor', max(1, base_qty * 0.5)))
                if qual_key in ('t2', 'faction'):
                    recipes.append((item_id, 'targeting_array', max(1, base_qty * 0.5)))

    # ── Engineering ──
    for base_id, name, base_price, desc in ENGINEERING:
        for size_key, size_data in SIZES.items():
            for qual_key, qual_data in QUALITIES.items():
                item_id = generate_item_id(base_id, size_key, qual_key)
                item_name = generate_item_name(name, size_key, qual_key)
                price = calc_price(base_price, size_key, qual_key)
                stats = {'size': size_key, 'quality': qual_key, 'slot': 'low'}
                items.append((item_id, item_name, price, 5, size_data['volume'], 1.0, desc, 'Engineering', stats))
                base_qty = size_data['price_mult']
                recipes.append((item_id, 'cap_cell', max(1, base_qty)))
                recipes.append((item_id, 'microprocessor', max(1, base_qty * 0.3)))
                if qual_key in ('t2', 'faction'):
                    recipes.append((item_id, 'reactor_core', max(1, base_qty * 0.2)))

    # ── Drones (S/M/L only, no Capital) ──
    drone_sizes = {'S': 'Light', 'M': 'Medium', 'L': 'Heavy'}
    for base_id, name, base_price, dmg_type, desc in DRONES:
        for size_key, size_label in drone_sizes.items():
            for qual_key, qual_data in QUALITIES.items():
                item_id = generate_item_id(base_id, size_key, qual_key)
                item_name = f"{size_label} {name}" if qual_key == 'standard' else f"{size_label} {generate_item_name(name, size_key, qual_key).split('(')[0].strip()}"
                price = calc_price(base_price, size_key, qual_key)
                stats = {'damage_type': dmg_type, 'size': size_key, 'quality': qual_key, 'drone_size': size_label}
                items.append((item_id, item_name, price, 5, SIZES[size_key]['volume'] * 0.5, 1.0, desc, 'Drones', stats))
                base_qty = SIZES[size_key]['price_mult']
                recipes.append((item_id, 'drone_cpu', max(1, base_qty)))
                recipes.append((item_id, 'microprocessor', max(1, base_qty * 0.5)))
                if qual_key in ('t2', 'faction'):
                    recipes.append((item_id, 'sensor_cluster', max(1, base_qty * 0.3)))

    # ── Ammunition ──
    ammo_qual = {'standard': 1.0, 'faction': 2.5, 't2': 4.0}
    for weapon_id, ammo_list in AMMO_TYPES.items():
        for ammo_variant, ammo_name, dmg_type in ammo_list:
            for size_key, size_data in SIZES.items():
                for qual_key, qual_mult in ammo_qual.items():
                    item_id = f"ammo_{weapon_id}_{ammo_variant}_{size_key.lower()}"
                    if qual_key != 'standard':
                        item_id += f"_{qual_key}"
                    size_label = SIZES[size_key]['label']
                    if qual_key == 'standard':
                        display_name = f"{ammo_name} ({size_label})"
                    elif qual_key == 'faction':
                        display_name = f"Navy {ammo_name} ({size_label})"
                    else:
                        display_name = f"{ammo_name} II ({size_label})"
                    base_ammo_price = 100 * size_data['price_mult'] * qual_mult
                    stats = {'damage_type': dmg_type, 'size': size_key, 'quality': qual_key, 'for_weapon': weapon_id}
                    items.append((item_id, display_name, base_ammo_price, 5, 0.01 * size_data['volume'], 0.8, f"Ammunition for {weapon_id}", 'Ammunition', stats))
                    # Ammo recipes: simple mineral inputs
                    recipes.append((item_id, 'refined_titanium', max(1, size_data['price_mult'] * 0.5 * qual_mult)))
                    if qual_key != 'standard':
                        recipes.append((item_id, 'refined_copper', max(1, size_data['price_mult'] * 0.3)))

    # ── Mining Equipment (S/M/L only) ──
    mine_sizes = {k: v for k, v in SIZES.items() if k != 'C'}
    for base_id, name, base_price, desc in MINING:
        for size_key, size_data in mine_sizes.items():
            for qual_key, qual_data in QUALITIES.items():
                item_id = generate_item_id(base_id, size_key, qual_key)
                item_name = generate_item_name(name, size_key, qual_key)
                price = calc_price(base_price, size_key, qual_key)
                stats = {'size': size_key, 'quality': qual_key, 'slot': 'high'}
                items.append((item_id, item_name, price, 5, size_data['volume'], 1.0, desc, 'Mining', stats))
                base_qty = size_data['price_mult']
                recipes.append((item_id, 'microprocessor', max(1, base_qty)))
                recipes.append((item_id, 'refined_titanium', max(1, base_qty * 2)))

    # ── Insert into database ──
    print(f"Inserting {len(items)} items and {len(recipes)} recipe entries...")

    # Add category column if not exists
    cols = [r[1] for r in conn.execute('PRAGMA table_info(commodities)')]
    if 'category' not in cols:
        conn.execute("ALTER TABLE commodities ADD COLUMN category TEXT DEFAULT ''")

    for item_id, name, price, tier, volume, elasticity, desc, category, stats in items:
        conn.execute("""INSERT OR REPLACE INTO commodities 
            (id, name, base_price, tier, volume, elasticity, description, category, stats)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (item_id, name, price, tier, volume, elasticity, desc, category, json.dumps(stats)))

    for commodity_id, input_id, quantity in recipes:
        conn.execute("INSERT OR REPLACE INTO recipes (commodity_id, input_id, quantity) VALUES (?, ?, ?)",
            (commodity_id, input_id, round(quantity, 2)))

    conn.commit()

    # Final count
    total = conn.execute("SELECT COUNT(*) FROM commodities").fetchone()[0]
    recipe_count = conn.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    print(f"Done! Total items in DB: {total}, recipes: {recipe_count}")

    # Verify no broken recipe references
    broken = conn.execute("""
        SELECT r.commodity_id, r.input_id FROM recipes r
        LEFT JOIN commodities c ON r.input_id = c.id
        WHERE c.id IS NULL
    """).fetchall()
    if broken:
        print(f"WARNING: {len(broken)} recipe entries reference missing items!")
        for b in broken[:5]:
            print(f"  {b[0]} needs {b[1]} (missing)")
    else:
        print("All recipe references valid.")

    conn.close()



if __name__ == '__main__':
    generate_all()
