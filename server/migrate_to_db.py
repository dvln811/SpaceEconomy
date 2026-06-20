"""Migrate all game data from Python modules into game_data.db."""
import json
import re

from server.game_data_db import get_data_db, init_data_schema
from server.models import COMMODITIES, STATION_CONSUMPTION
from server.factions import FACTIONS, SYSTEM_FACTIONS
from server.ship_types import HAULER_SHIPS, MINER_SHIPS, MILITARY_SHIPS as CIVILIAN_MILITARY_SHIPS
from server.military import MILITARY_SHIPS, FLEET_TARGETS
from server.universe import build_universe


def _slug(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


def migrate():
    conn = get_data_db()
    init_data_schema(conn)
    cur = conn.cursor()

    # ── Factions & Corporations ───────────────────────────────────────────
    print("Inserting factions...")
    for fid, f in FACTIONS.items():
        cur.execute("INSERT OR REPLACE INTO factions (id, name, short, philosophy, home_cluster, allies, enemies, color) VALUES (?,?,?,?,?,?,?,?)",
                    (fid, f.name, f.short, f.philosophy, f.home_cluster, json.dumps(f.allies), json.dumps(f.enemies), f.color))
        for corp in f.corporations:
            cur.execute("INSERT OR REPLACE INTO corporations (id, name, faction_id, focus, description) VALUES (?,?,?,?,?)",
                        (corp.id, corp.name, corp.faction_id, corp.focus, corp.description))
    print(f"  {len(FACTIONS)} factions, {sum(len(f.corporations) for f in FACTIONS.values())} corporations")

    # ── Commodities & Recipes ─────────────────────────────────────────────
    print("Inserting commodities...")
    for cid, c in COMMODITIES.items():
        cur.execute("INSERT OR REPLACE INTO commodities (id, name, base_price, tier, volume, elasticity, description, stats) VALUES (?,?,?,?,?,?,?,?)",
                    (cid, c.name, c.base_price, c.tier, c.volume, c.elasticity, c.description, json.dumps(c.stats)))
        for input_id, qty in c.recipe.items():
            cur.execute("INSERT OR REPLACE INTO recipes (commodity_id, input_id, quantity) VALUES (?,?,?)",
                        (cid, input_id, qty))
    print(f"  {len(COMMODITIES)} commodities")

    # ── Systems, Stations, Asteroid Fields, Objects ───────────────────────
    print("Inserting systems...")
    universe = build_universe()
    station_count = 0
    field_count = 0
    obj_count = 0

    # Insert all systems first (connections reference other systems)
    for sid, sys in universe.items():
        faction_id = SYSTEM_FACTIONS.get(sid, sys.faction or "")
        cur.execute("INSERT OR REPLACE INTO systems (id, name, system_type, cluster, security, faction_id, x, y, z) VALUES (?,?,?,?,?,?,?,?,?)",
                    (sid, sys.name, sys.system_type, sys.cluster, sys.security, faction_id, sys.x, sys.y, sys.z))

    # Now insert connections and sub-objects
    for sid, sys in universe.items():
        for conn_id in sys.connections:
            cur.execute("INSERT OR REPLACE INTO system_connections (from_id, to_id) VALUES (?,?)", (sid, conn_id))

        for st in sys.stations:
            st_id = f"{sid}_{_slug(st.name)}"
            cur.execute("INSERT OR REPLACE INTO stations (id, name, system_id, station_type, production_rate) VALUES (?,?,?,?,?)",
                        (st_id, st.name, sid, st.station_type, st.production_rate))
            for prod in st.produces:
                cur.execute("INSERT OR REPLACE INTO station_produces (station_id, commodity_id) VALUES (?,?)", (st_id, prod))
            station_count += 1

        for af in sys.asteroid_fields:
            af_id = f"{sid}_{_slug(af.name)}"
            cur.execute("INSERT OR REPLACE INTO asteroid_fields (id, name, system_id, field_type, density, danger) VALUES (?,?,?,?,?,?)",
                        (af_id, af.name, sid, af.field_type, af.density, af.danger))
            for y in af.yields:
                cur.execute("INSERT OR REPLACE INTO field_yields (field_id, commodity_id) VALUES (?,?)", (af_id, y))
            field_count += 1

        for obj in sys.objects:
            cur.execute("INSERT OR REPLACE INTO system_objects (id, name, system_id, obj_type, distance, angle, parent, connects_to) VALUES (?,?,?,?,?,?,?,?)",
                        (obj.id, obj.name, sid, obj.obj_type, obj.distance, obj.angle, obj.parent, obj.connects_to))
            obj_count += 1

    print(f"  {len(universe)} systems, {station_count} stations, {field_count} asteroid fields, {obj_count} objects")

    # ── Civilian Ship Types ───────────────────────────────────────────────
    print("Inserting civilian ship types...")
    all_civilian = {**HAULER_SHIPS, **MINER_SHIPS, **CIVILIAN_MILITARY_SHIPS}
    for ship_id, s in all_civilian.items():
        cur.execute("INSERT OR REPLACE INTO ship_types (id, name, role, tier, cargo_capacity, fuel_capacity, speed, intra_speed, hull_hp, align_time, hardpoints, build_cost, description) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (ship_id, s.name, s.role, s.tier, s.cargo_capacity, s.fuel_capacity, s.speed, s.intra_speed, s.hull_hp, s.align_time, json.dumps(s.hardpoints), json.dumps(s.build_cost), s.description))
    print(f"  {len(all_civilian)} ship types")

    # ── Military Ships & Fleet Targets ────────────────────────────────────
    print("Inserting military ships...")
    for ship_id, m in MILITARY_SHIPS.items():
        cur.execute("INSERT OR REPLACE INTO military_ships (id, name, hull_class, faction_id, hull_hp, armor_hp, shield_hp, crew, weapons, modules, build_cost, description) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (ship_id, m.name, m.hull_class, m.faction, m.hull_hp, m.armor_hp, m.shield_hp, m.crew, json.dumps(m.weapons), json.dumps(m.modules), json.dumps(m.build_cost), m.description))
    print(f"  {len(MILITARY_SHIPS)} military ships")

    print("Inserting fleet targets...")
    ft_count = 0
    for faction_id, targets in FLEET_TARGETS.items():
        for ship_id, count in targets.items():
            cur.execute("INSERT OR REPLACE INTO fleet_targets (faction_id, ship_id, target_count) VALUES (?,?,?)",
                        (faction_id, ship_id, count))
            ft_count += 1
    print(f"  {ft_count} fleet target entries")

    # ── Station Consumption ───────────────────────────────────────────────
    print("Inserting station consumption...")
    sc_count = 0
    for station_type, commodities in STATION_CONSUMPTION.items():
        for cid in commodities:
            cur.execute("INSERT OR REPLACE INTO station_consumption (station_type, commodity_id) VALUES (?,?)",
                        (station_type, cid))
            sc_count += 1
    print(f"  {sc_count} station consumption entries")

    conn.commit()
    conn.close()
    print("\nMigration complete!")


if __name__ == "__main__":
    migrate()
