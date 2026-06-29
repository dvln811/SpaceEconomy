"""Data access layer: loads game data from game_data.db instead of Python constants.
Drop-in replacement for the old hardcoded data."""
import json
from server.game_data_db import get_data_db, GAME_DATA_DB
from server.models import Commodity, AsteroidField, SystemObject, Station, System
import os


def load_commodities(conn=None) -> dict:
    """Load all commodities with recipes from DB. Returns dict matching COMMODITIES format."""
    close = False
    if conn is None:
        conn = get_data_db()
        close = True

    commodities = {}
    rows = conn.execute("SELECT * FROM commodities").fetchall()
    for row in rows:
        cid = row["id"]
        # Load recipe
        recipe_rows = conn.execute("SELECT input_id, quantity FROM recipes WHERE commodity_id=?", (cid,)).fetchall()
        recipe = {r["input_id"]: r["quantity"] for r in recipe_rows}
        stats = json.loads(row["stats"]) if row["stats"] else {}

        commodities[cid] = Commodity(
            name=row["name"],
            base_price=row["base_price"],
            tier=row["tier"],
            volume=row["volume"],
            elasticity=row["elasticity"],
            description=row["description"],
            recipe=recipe,
            stats=stats,
        )

    if close:
        conn.close()
    return commodities


def load_station_consumption(conn=None) -> dict:
    """Load station consumption data. Returns dict matching STATION_CONSUMPTION format."""
    close = False
    if conn is None:
        conn = get_data_db()
        close = True

    consumption = {}
    rows = conn.execute("SELECT station_type, commodity_id FROM station_consumption").fetchall()
    for row in rows:
        st = row["station_type"]
        if st not in consumption:
            consumption[st] = []
        consumption[st].append(row["commodity_id"])

    if close:
        conn.close()
    return consumption


def load_factions(conn=None) -> dict:
    """Load factions with corporations."""
    close = False
    if conn is None:
        conn = get_data_db()
        close = True

    factions = {}
    rows = conn.execute("SELECT * FROM factions").fetchall()
    for row in rows:
        corps = conn.execute("SELECT * FROM corporations WHERE faction_id=? AND status='active'", (row["id"],)).fetchall()
        factions[row["id"]] = {
            "id": row["id"], "name": row["name"], "short": row["short"],
            "philosophy": row["philosophy"], "home_cluster": row["home_cluster"],
            "allies": json.loads(row["allies"]), "enemies": json.loads(row["enemies"]),
            "color": row["color"],
            "history": row["history"] if "history" in row.keys() else "",
            "lore": row["lore"] if "lore" in row.keys() else "",
            "corporations": [{"id": c["id"], "name": c["name"], "emblem": c["emblem"], "specialty": c["specialty"], "head_agent_id": c["head_agent_id"], "history": c["history"] or "", "members": c["members"] or 0, "stations": json.loads(c["stations"] or "[]")} for c in corps],
        }

    if close:
        conn.close()
    return factions


def load_universe(conn=None) -> dict:
    """Load full universe from DB. Returns dict matching build_universe() format."""
    close = False
    if conn is None:
        conn = get_data_db()
        close = True

    universe = {}
    systems = conn.execute("SELECT * FROM systems").fetchall()

    for sys_row in systems:
        sid = sys_row["id"]

        # Connections
        conns = conn.execute("SELECT to_id FROM system_connections WHERE from_id=?", (sid,)).fetchall()
        connections = [c["to_id"] for c in conns]

        # Stations
        station_rows = conn.execute("SELECT * FROM stations WHERE system_id=?", (sid,)).fetchall()
        stations = []
        for st_row in station_rows:
            produces_rows = conn.execute("SELECT commodity_id FROM station_produces WHERE station_id=?", (st_row["id"],)).fetchall()
            produces = [p["commodity_id"] for p in produces_rows]
            stations.append(Station(
                name=st_row["name"], system_id=sid,
                station_type=st_row["station_type"],
                produces=produces,
                production_rate=st_row["production_rate"],
            ))

        # Asteroid fields
        field_rows = conn.execute("SELECT * FROM asteroid_fields WHERE system_id=?", (sid,)).fetchall()
        fields = []
        for f_row in field_rows:
            yield_rows = conn.execute("SELECT commodity_id FROM field_yields WHERE field_id=?", (f_row["id"],)).fetchall()
            yields = [y["commodity_id"] for y in yield_rows]
            fields.append(AsteroidField(
                name=f_row["name"], field_type=f_row["field_type"],
                yields=yields, density=f_row["density"], danger=f_row["danger"],
            ))

        # System objects
        obj_rows = conn.execute("SELECT * FROM system_objects WHERE system_id=?", (sid,)).fetchall()
        objects = [SystemObject(
            id=o["id"], name=o["name"], obj_type=o["obj_type"],
            distance=o["distance"], angle=o["angle"],
            parent=o["parent"], connects_to=o["connects_to"],
        ) for o in obj_rows]

        universe[sid] = System(
            id=sid, name=sys_row["name"], system_type=sys_row["system_type"],
            cluster=sys_row["cluster"], security=sys_row["security"],
            sec_level=sys_row["sec_level"] if "sec_level" in sys_row.keys() else 0.0,
            population=sys_row["population"] if "population" in sys_row.keys() else 0,
            faction=sys_row["faction_id"],
            region=sys_row["region"] if "region" in sys_row.keys() else "",
            x=sys_row["x"], y=sys_row["y"], z=sys_row["z"],
            stations=stations, asteroid_fields=fields,
            connections=connections, objects=objects,
        )

    if close:
        conn.close()
    return universe


def load_ship_types(conn=None) -> dict:
    """Load non-faction ships from unified ships table."""
    close = False
    if conn is None:
        conn = get_data_db()
        close = True

    from server.ship_types import ShipType
    ships = {}
    rows = conn.execute("SELECT * FROM ships WHERE faction_id = ''").fetchall()
    for row in rows:
        ships[row["id"]] = ShipType(
            id=row["id"], name=row["name"], role=row["hull_class"], tier=row["tier"],
            cargo_capacity=row["cargo_capacity"], fuel_capacity=row["fuel_capacity"],
            speed=row["speed"], intra_speed=row["intra_speed"],
            hull_hp=row["hull_hp"], align_time=row["align_time"],
            hardpoints=json.loads(row["hardpoints"]),
            build_cost=json.loads(row["build_cost"]),
            description=row["description"],
        )

    if close:
        conn.close()
    return ships


def load_military_ships(conn=None) -> dict:
    """Load faction military ships from unified ships table."""
    close = False
    if conn is None:
        conn = get_data_db()
        close = True

    from server.military import MilitaryShipClass
    ships = {}
    rows = conn.execute("SELECT * FROM ships WHERE faction_id != ''").fetchall()
    for row in rows:
        ships[row["id"]] = MilitaryShipClass(
            id=row["id"], name=row["name"], hull_class=row["hull_class"],
            faction=row["faction_id"],
            hull_hp=row["hull_hp"], armor_hp=row["armor_hp"], shield_hp=row["shield_hp"],
            crew=row["crew"],
            weapons=json.loads(row["weapons"]),
            modules=json.loads(row["modules"]),
            build_cost=json.loads(row["build_cost"]),
            fitting_cost=json.loads(row["fitting_cost"]) if row["fitting_cost"] else {},
            description=row["description"],
        )

    if close:
        conn.close()
    return ships


def load_fleet_targets(conn=None) -> dict:
    """Load fleet target counts per faction."""
    close = False
    if conn is None:
        conn = get_data_db()
        close = True

    targets = {}
    rows = conn.execute("SELECT * FROM fleet_targets").fetchall()
    for row in rows:
        fid = row["faction_id"]
        if fid not in targets:
            targets[fid] = {}
        targets[fid][row["ship_id"]] = row["target_count"]

    if close:
        conn.close()
    return targets


def is_db_ready() -> bool:
    """Check if game_data.db exists and has data."""
    if not os.path.exists(GAME_DATA_DB):
        return False
    try:
        conn = get_data_db()
        count = conn.execute("SELECT COUNT(*) FROM commodities").fetchone()[0]
        conn.close()
        return count > 0
    except:
        return False
