"""Add ship variants to the game database.
For each faction: 1 extra variant per military hull class (Fighter-Battleship).
Plus 1 additional Carrier variant for terran_fed."""
import sqlite3
import json
import random
import os

DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
DB_PATH = os.path.join(DATA_DIR, "game_data.db")

# Variant names per hull class
VARIANT_NAMES = {
    "Fighter": {"terran_fed": ("tf_assault_fighter", "Falco"), "iron_compact": ("ic_heavy_fighter", "Spike"), "free_states": ("fa_strike_fighter", "Dart"), "merchants_guild": ("mg_patrol_fighter", "Sentinel"), "science_collective": ("nc_phase_fighter", "Photon"), "corsairs": ("crs_ambush_fighter", "Viper")},
    "Frigate": {"terran_fed": ("tf_assault_frigate", "Gladius"), "iron_compact": ("ic_heavy_frigate", "Mace"), "free_states": ("fa_strike_frigate", "Stinger"), "merchants_guild": ("mg_patrol_frigate", "Guardian"), "science_collective": ("nc_phase_frigate", "Quark"), "corsairs": ("crs_ambush_frigate", "Jackal")},
    "Destroyer": {"terran_fed": ("tf_assault_destroyer", "Vanguard"), "iron_compact": ("ic_heavy_destroyer", "Maul"), "free_states": ("fa_strike_destroyer", "Tempest"), "merchants_guild": ("mg_patrol_destroyer", "Warden"), "science_collective": ("nc_phase_destroyer", "Helix"), "corsairs": ("crs_ambush_destroyer", "Wraith")},
    "Cruiser": {"terran_fed": ("tf_assault_cruiser", "Legatus"), "iron_compact": ("ic_heavy_cruiser", "Bastion"), "free_states": ("fa_strike_cruiser", "Cyclone"), "merchants_guild": ("mg_patrol_cruiser", "Arbiter"), "science_collective": ("nc_phase_cruiser", "Catalyst"), "corsairs": ("crs_ambush_cruiser", "Phantom")},
    "Battlecruiser": {"terran_fed": ("tf_assault_battlecruiser", "Proconsul"), "iron_compact": ("ic_heavy_battlecruiser", "Rampart"), "free_states": ("fa_strike_battlecruiser", "Hurricane"), "merchants_guild": ("mg_patrol_battlecruiser", "Regent"), "science_collective": ("nc_phase_battlecruiser", "Postulate"), "corsairs": ("crs_ambush_battlecruiser", "Ravager")},
    "Battleship": {"terran_fed": ("tf_assault_battleship", "Dictator"), "iron_compact": ("ic_heavy_battleship", "Devastator"), "free_states": ("fa_strike_battleship", "Cataclysm"), "merchants_guild": ("mg_patrol_battleship", "Chancellor"), "science_collective": ("nc_phase_battleship", "Apotheosis"), "corsairs": ("crs_ambush_battleship", "Tyrant")},
}

# Extra carrier: terran_fed
EXTRA_CARRIER = ("tf_carrier", "Olympus", "terran_fed")


def tweak(val, pct=10):
    """Tweak a numeric value by +/-pct%."""
    factor = 1.0 + random.uniform(-pct/100, pct/100)
    if isinstance(val, int):
        return max(1, int(val * factor))
    return round(val * factor, 2)


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    random.seed(42)

    # Get existing faction ships as base templates
    existing = {}
    rows = conn.execute("SELECT * FROM ships WHERE faction_id != ''").fetchall()
    for r in rows:
        key = (r["faction_id"], r["hull_class"])
        existing[key] = dict(r)

    inserted = 0
    for hull_class, factions in VARIANT_NAMES.items():
        for faction_id, (ship_id, ship_name) in factions.items():
            base = existing.get((faction_id, hull_class))
            if not base:
                print(f"  SKIP: no base for {faction_id}/{hull_class}")
                continue
            # Check if already exists
            if conn.execute("SELECT 1 FROM ships WHERE id=?", (ship_id,)).fetchone():
                continue
            conn.execute("""INSERT INTO ships (id, name, hull_class, faction_id, tier, hull_hp, armor_hp, shield_hp,
                cargo_capacity, fuel_capacity, speed, intra_speed, align_time, crew,
                hardpoints, weapons, modules, build_cost, build_time, description)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                ship_id, ship_name, hull_class, faction_id, base["tier"],
                tweak(base["hull_hp"]), tweak(base["armor_hp"]), tweak(base["shield_hp"]),
                base["cargo_capacity"], tweak(base["fuel_capacity"]),
                tweak(base["speed"]), tweak(base["intra_speed"]), tweak(base["align_time"]),
                tweak(base["crew"]),
                base["hardpoints"], base["weapons"], base["modules"],
                base["build_cost"], base["build_time"] or 10,
                f"Variant of {base['name']}"
            ))
            inserted += 1

    # Extra carrier for terran_fed (based on science_collective's carrier)
    carrier_base = existing.get(("science_collective", "Carrier"))
    if carrier_base and not conn.execute("SELECT 1 FROM ships WHERE id=?", (EXTRA_CARRIER[0],)).fetchone():
        conn.execute("""INSERT INTO ships (id, name, hull_class, faction_id, tier, hull_hp, armor_hp, shield_hp,
            cargo_capacity, fuel_capacity, speed, intra_speed, align_time, crew,
            hardpoints, weapons, modules, build_cost, build_time, description)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            EXTRA_CARRIER[0], EXTRA_CARRIER[1], "Carrier", EXTRA_CARRIER[2], carrier_base["tier"],
            tweak(carrier_base["hull_hp"]), tweak(carrier_base["armor_hp"]), tweak(carrier_base["shield_hp"]),
            carrier_base["cargo_capacity"], tweak(carrier_base["fuel_capacity"]),
            tweak(carrier_base["speed"]), tweak(carrier_base["intra_speed"]), tweak(carrier_base["align_time"]),
            tweak(carrier_base["crew"]),
            carrier_base["hardpoints"], carrier_base["weapons"], carrier_base["modules"],
            carrier_base["build_cost"], carrier_base["build_time"] or 20,
            "Terran Federation carrier"
        ))
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Inserted {inserted} ship variants.")


if __name__ == "__main__":
    run()
