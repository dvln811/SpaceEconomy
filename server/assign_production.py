"""Assign the full 1540-item catalog to station production.
Each station type gets items from appropriate categories.
Items are distributed so not every station makes everything."""
import sqlite3
import json
import os
import random

random.seed(42)

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "game_data.db")

# Category -> station_type mapping
CATEGORY_STATION = {
    "Materials": {
        "Raw Materials": "mining_colony",
        "Refined Materials": "refinery",
        "Components": "component_works",
        "Manufactured": "component_works",
    },
    "Weapons": {
        "Turrets": "factory",
        "Energy Weapons": "factory",
        "Launchers": "factory",
    },
    "Ammunition": {
        "Projectile Ammo": "factory",
        "Hybrid Charges": "factory",
        "Energy Crystals": "factory",
        "Energy Cells": "factory",
        "Magnetic Ammo": "factory",
        "Missiles": "factory",
    },
    "Ship Equipment": {
        "Armor": "component_works",
        "Shields": "component_works",
        "Engineering": "component_works",
        "Propulsion": "component_works",
        "Navigation": "component_works",
        "Electronics": "component_works",
        "Electronic Warfare": "factory",
        "Energy Warfare": "factory",
        "Tackle": "component_works",
        "Hull": "component_works",
        "Mining": "component_works",
        "Remote Repair": "component_works",
        "Drones": "factory",
    },
    "Drones": {
        "Combat Drones": "factory",
        "Utility Drones": "factory",
        "Logistics Drones": "factory",
        "Electronic Warfare Drones": "factory",
    },
    "Trade Goods": {
        "Commodities": "trade_hub",
    },
}

# How many items each station should produce (don't overload)
MAX_PRODUCES_PER_STATION = 12


def assign_production():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Load all items with their categories
    items = conn.execute(
        "SELECT id, category, subcategory, group_name FROM commodities"
    ).fetchall()

    # Load stations
    stations = conn.execute(
        "SELECT id, station_type, system_id FROM stations"
    ).fetchall()

    # Group stations by type
    stations_by_type = {}
    for st in stations:
        stype = st["station_type"]
        if stype not in stations_by_type:
            stations_by_type[stype] = []
        stations_by_type[stype].append(st["id"])

    print("Stations by type:")
    for k, v in stations_by_type.items():
        print(f"  {k}: {len(v)}")

    # Group items by target station type
    items_for_type = {}  # {station_type: [item_ids]}
    unassigned = []
    for item in items:
        cat = item["category"]
        subcat = item["subcategory"]
        target_type = None
        if cat in CATEGORY_STATION:
            target_type = CATEGORY_STATION[cat].get(subcat)
        if target_type:
            if target_type not in items_for_type:
                items_for_type[target_type] = []
            items_for_type[target_type].append(item["id"])
        else:
            unassigned.append((item["id"], cat, subcat))

    print("\nItems per station type:")
    for k, v in items_for_type.items():
        print(f"  {k}: {len(v)} items")
    if unassigned:
        print(f"  UNASSIGNED: {len(unassigned)}")
        for u in unassigned[:5]:
            print(f"    {u}")

    # Distribute items across stations of the right type
    # Strategy: round-robin assign items to stations, capped at MAX per station
    conn.execute("DELETE FROM station_produces")

    total_assignments = 0
    for stype, item_ids in items_for_type.items():
        available_stations = stations_by_type.get(stype, [])
        if not available_stations:
            print(f"  WARNING: no stations of type {stype} for {len(item_ids)} items!")
            # Fallback to factory
            available_stations = stations_by_type.get("factory", [])

        random.shuffle(item_ids)
        random.shuffle(available_stations)

        # Distribute evenly
        for i, item_id in enumerate(item_ids):
            station_id = available_stations[i % len(available_stations)]
            conn.execute(
                "INSERT INTO station_produces (station_id, commodity_id) VALUES (?, ?)",
                (station_id, item_id)
            )
            total_assignments += 1

    conn.commit()

    # Verify
    check = conn.execute("SELECT count(*) FROM station_produces").fetchone()[0]
    unique_items = conn.execute("SELECT count(DISTINCT commodity_id) FROM station_produces").fetchone()[0]
    print(f"\nDone: {check} total assignments, {unique_items} unique items assigned")

    # Check distribution
    overloaded = conn.execute(
        "SELECT station_id, count(*) as c FROM station_produces GROUP BY station_id ORDER BY c DESC LIMIT 5"
    ).fetchall()
    print(f"Heaviest stations: {[(r[0][:10], r[1]) for r in overloaded]}")

    conn.close()


if __name__ == "__main__":
    assign_production()
