import os
import threading
import time
import logging
from flask import Flask, send_from_directory, jsonify, request
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("space_economy")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Always deploy the shipped game_data.db to DATA_DIR (volume may have stale copy)
_data_dir = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(_data_dir, exist_ok=True)
_shipped_db = os.path.join(BASE_DIR, "game_data_shipped.db")
_live_db = os.path.join(_data_dir, "game_data.db")
if os.path.exists(_shipped_db):
    import shutil
    shutil.copy2(_shipped_db, _live_db)
    log.info("Deployed fresh game_data.db to volume")
    # Also copy tag files needed by generators
    for _tag_file in ("portrait_tags_shipped.json", "emblem_tags_shipped.json"):
        _src = os.path.join(BASE_DIR, _tag_file)
        _dst = os.path.join(_data_dir, _tag_file.replace("_shipped", ""))
        if os.path.exists(_src):
            shutil.copy2(_src, _dst)

app = Flask(__name__, static_folder=None)

# ── Simulation (deferred init for fast startup) ────────────────────────────────
from server.simulation import Simulation, COMMODITIES, STATION_CONSUMPTION
from server.persistence import init_db, save_simulation, load_simulation, clear_db
from server.supervisor import Supervisor
from server.workers.economy import EconomyWorker
from server.workers.npc_decisions import NPCDecisionWorker
from server.workers.faction_strategy import FactionStrategyWorker
from server.workers.battle_sim import BattleSimWorker
from server.workers.corsair_spawn import CorsairSpawnWorker
from server.workers.dashboard import DashboardWorker

sim = None
supervisor = None
sim_speed = {"rate": float(os.getenv("TICK_RATE", "1.0")), "multiplier": 1}
_sim_ready = threading.Event()


def _init_simulation():
    """Background init: loads universe, spawns ships, starts supervisor."""
    global sim, supervisor
    init_db()
    sim = Simulation()
    if load_simulation(sim):
        log.info(f"Loaded saved state at tick {sim.tick_count}")
    else:
        log.info("No saved state found, starting fresh")

    # Backfill risk_tolerance for ships loaded from old saves
    _trader_factions = ["Trade Guild", "Free Traders", "Industrial Corp", "Agrarian League", "Frontier Logistics"]
    _miner_factions = ["Miners Union", "Deep Rock Corp", "Frontier Logistics"]
    for _i, _s in enumerate(sim.ships):
        if not hasattr(_s, 'risk_tolerance') or _s.risk_tolerance == 0:
            _s.risk_tolerance = 0.5
        if not _s.faction:
            if _s.role == "miner":
                _s.faction = _miner_factions[_i % len(_miner_factions)]
            else:
                _s.faction = _trader_factions[_i % len(_trader_factions)]
        if _s.name and not any(c.isdigit() for c in _s.name):
            import random as _rnd
            prefix = "HLR" if _s.role != "miner" else "MNR"
            _s.name = f"{_s.ship_class} {prefix}-{_rnd.randint(1000,9999)}"

    # Start supervisor with workers
    supervisor = Supervisor(sim)
    supervisor.tick_rate = sim_speed["rate"]
    supervisor.multiplier = sim_speed["multiplier"]
    supervisor.add_worker(EconomyWorker(COMMODITIES, STATION_CONSUMPTION))
    supervisor.add_worker(NPCDecisionWorker(COMMODITIES))
    supervisor.add_worker(FactionStrategyWorker())
    supervisor.add_worker(BattleSimWorker())
    supervisor.add_worker(CorsairSpawnWorker())
    supervisor.add_worker(DashboardWorker(COMMODITIES, STATION_CONSUMPTION))
    supervisor.start()
    log.info(f"Supervisor started ({sim_speed['rate']}s/tick, {len(sim.ships)} NPCs, 6 workers)")
    _sim_ready.set()


threading.Thread(target=_init_simulation, daemon=True).start()


# ── Routes ─────────────────────────────────────────────────────────────────────
def _build_order_book(st):
    """Generate buy/sell orders for a station."""
    from server.simulation import COMMODITIES as COMS, STATION_CONSUMPTION
    sell_orders = []
    buy_orders = []
    for commodity_id, qty in st.inventory.items():
        if qty > 1 and commodity_id in COMS:
            market_price = st.price_cache.get(commodity_id, 0)
            base = COMS[commodity_id].base_price
            price = max(market_price, base) if market_price > 0 else base
            if price > 0:
                sell_orders.append({"commodity": commodity_id, "qty": int(qty), "price": round(price, 2)})
    for prod_id in st.produces:
        com = COMS.get(prod_id)
        if not com or not com.recipe:
            continue
        for inp_id, qty_needed in com.recipe.items():
            want = qty_needed * st.production_rate * 100
            have = st.inventory.get(inp_id, 0)
            deficit = want - have
            if deficit > 0 and inp_id in COMS:
                base = COMS[inp_id].base_price
                market = st.price_cache.get(inp_id, 0)
                buy_price = min(max(market, base) * 1.05, base * 2)
                buy_orders.append({"commodity": inp_id, "qty": int(deficit), "price": round(buy_price, 2)})
    for commodity_id in STATION_CONSUMPTION.get(st.station_type, []):
        have = st.inventory.get(commodity_id, 0)
        if have < 500 and commodity_id in COMS:
            base = COMS[commodity_id].base_price
            market = st.price_cache.get(commodity_id, 0)
            buy_price = min(max(market, base) * 1.1, base * 2)
            buy_orders.append({"commodity": commodity_id, "qty": int(500 - have), "price": round(buy_price, 2)})
    return sorted(sell_orders, key=lambda x: -x["qty"])[:20], sorted(buy_orders, key=lambda x: -x["qty"])[:50]


def _get_project_buy_orders():
    """Generate buy orders from active build projects, cascaded through recipes."""
    from server.simulation import COMMODITIES as COMS
    from server.game_data_db import get_data_db
    conn = get_data_db()
    projects = conn.execute("SELECT target_system, requirements, accumulated FROM build_projects WHERE status='active'").fetchall()
    conn.close()
    # {system_id: [{commodity, qty, price}]}
    orders_by_system = {}
    for p in projects:
        target = p['target_system']
        reqs = json.loads(p['requirements'])
        accumulated = json.loads(p['accumulated'])
        if target not in orders_by_system:
            orders_by_system[target] = []
        for mat_id, qty_needed in reqs.items():
            have = accumulated.get(mat_id, 0)
            deficit = qty_needed - have
            if deficit > 0:
                price = COMS[mat_id].base_price * 1.2 if mat_id in COMS else 1000
                orders_by_system[target].append({"commodity": mat_id, "qty": int(deficit), "price": round(price, 2)})
                com = COMS.get(mat_id)
                if com and com.recipe:
                    for inp_id, inp_qty in com.recipe.items():
                        inp_need = inp_qty * deficit
                        inp_price = COMS[inp_id].base_price * 1.15 if inp_id in COMS else 100
                        orders_by_system[target].append({"commodity": inp_id, "qty": int(inp_need), "price": round(inp_price, 2)})
    return orders_by_system


_project_orders_cache = {}
_project_orders_tick = 0



@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "game.html")


@app.route("/design")
def design():
    return send_from_directory(BASE_DIR, "design.html")


@app.route("/universe")
def universe_page():
    return send_from_directory(BASE_DIR, "universe.html")


@app.route("/ships")
def ships_page():
    return send_from_directory(BASE_DIR, "ships.html")


@app.route("/sandbox")
def sandbox_page():
    return send_from_directory(BASE_DIR, "_sandbox2.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static"), filename)


@app.route("/market")
def market_page():
    return send_from_directory(BASE_DIR, "market.html")


@app.route("/resources")
def resources_page():
    return send_from_directory(BASE_DIR, "resources.html")


@app.route("/materials")
def materials_page():
    return send_from_directory(BASE_DIR, "materials.html")


@app.route("/products")
def products_page():
    return send_from_directory(BASE_DIR, "products.html")


@app.route("/fitting")
def fitting_page():
    return send_from_directory(BASE_DIR, "fitting.html")


@app.route("/items")
def items_page():
    return send_from_directory(BASE_DIR, "items.html")


@app.route("/ships_db")
def ships_db_page():
    return send_from_directory(BASE_DIR, "ships_db.html")


@app.route("/chain")
def chain_page():
    return send_from_directory(BASE_DIR, "chain.html")


@app.route("/ship")
def ship_page():
    return send_from_directory(BASE_DIR, "ship.html")


@app.route("/inventory")
def inventory_page():
    return send_from_directory(BASE_DIR, "inventory.html")


@app.route("/settings")
def settings_page():
    return send_from_directory(BASE_DIR, "settings.html")


@app.route("/docs")
def docs_page():
    return send_from_directory(BASE_DIR, "docs.html")


@app.route("/debug")
def debug_page():
    return send_from_directory(BASE_DIR, "debug.html")


@app.route("/system_view")
def system_view_page():
    return send_from_directory(BASE_DIR, "system_view.html")


@app.route("/health")
def health():
    if not _sim_ready.is_set():
        return {"status": "starting", "tick": 0}
    return {"status": "ok", "tick": sim.tick_count}


# ── API ────────────────────────────────────────────────────────────────────────

@app.before_request
def _check_sim_ready():
    """Return 503 for API calls if simulation hasn't finished loading."""
    if request.path.startswith('/api/') and not _sim_ready.is_set():
        return jsonify({"error": "Simulation loading, please wait..."}), 503


@app.route("/api/positions")
def api_positions():
    """Static system data: positions, connections, metadata. Fetched once by client."""
    systems = {}
    for sid, sys in sim.universe.items():
        systems[sid] = {
            "name": sys.name, "type": sys.system_type, "cluster": sys.cluster,
            "security": sys.security, "sec_level": sys.sec_level, "faction": sys.faction,
            "region": getattr(sys, 'region', ''),
            "x": sys.x, "y": sys.y, "z": sys.z,
            "connections": sys.connections,
            "station_count": len(sys.stations),
            "has_asteroids": len(sys.asteroid_fields) > 0,
        }
    return jsonify({"systems": systems})


@app.route("/api/market/orders")
def api_market_orders():
    """Buy/sell orders, optionally filtered by region."""
    region_filter = request.args.get('region', '')
    buy_orders = []
    sell_orders = []
    for sid, sys_obj in sim.universe.items():
        region = getattr(sys_obj, 'region', '')
        if region_filter and region != region_filter:
            continue
        for st in sys_obj.stations:
            sells, buys = _build_order_book(st)
            for o in sells:
                o['station'] = st.name
                o['system'] = sys_obj.name
                o['system_id'] = sid
                o['region'] = region
                sell_orders.append(o)
            for o in buys:
                o['station'] = st.name
                o['system'] = sys_obj.name
                o['system_id'] = sid
                o['region'] = region
                buy_orders.append(o)
    return jsonify({"tick": sim.tick_count, "region": region_filter, "buy_orders": buy_orders[:500], "sell_orders": sell_orders[:500]})


@app.route("/api/market/regions")
def api_market_regions():
    """List all regions."""
    regions = sorted(set(getattr(s, 'region', '') for s in sim.universe.values() if getattr(s, 'region', '')))
    return jsonify(regions)


@app.route("/api/market/ships")
def api_market_ships():
    """Ships available at shipyard stations with computed prices."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    rows = conn.execute("SELECT id, name, hull_class, build_cost, build_time FROM ships WHERE hull_class NOT IN ('Carrier','Dreadnought','Battleship') ORDER BY hull_class, name").fetchall()
    # Get base prices for cost calculation
    price_rows = conn.execute("SELECT id, base_price FROM commodities").fetchall()
    conn.close()
    base_prices = {r["id"]: r["base_price"] for r in price_rows}
    # Find shipyard stations
    shipyards = []
    for sid, sys_obj in sim.universe.items():
        for st in sys_obj.stations:
            if st.station_type == "shipyard":
                shipyards.append({"system": sys_obj.name, "station": st.name})
    result = []
    for r in rows:
        cost_data = json.loads(r["build_cost"]) if r["build_cost"] else {}
        price = sum(qty * base_prices.get(mat, 100) for mat, qty in cost_data.items())
        if price == 0:
            hull_mult = {"frigate": 50000, "destroyer": 150000, "cruiser": 500000, "battleship": 1500000, "industrial": 80000, "mining_barge": 60000}
            price = hull_mult.get(r["hull_class"], 100000)
        for yard in shipyards:
            result.append({"id": r["id"], "name": r["name"], "hull_class": r["hull_class"],
                           "price": round(price), "build_time": r["build_time"],
                           "shipyard_system": yard["system"], "shipyard_station": yard["station"]})
    return jsonify(result)


@app.route("/api/market/<system_id>")
def api_market(system_id):
    """Market data for a single system. Polled for the selected system only."""
    if system_id not in sim.universe:
        return jsonify({"error": "unknown system"}), 404
    sys_obj = sim.universe[system_id]
    stations = []
    for st in sys_obj.stations:
        sell_orders, buy_orders = _build_order_book(st)
        stations.append({
            "name": st.name, "station_type": st.station_type,
            "sell_orders": sell_orders, "buy_orders": buy_orders,
        })
    return jsonify({"id": system_id, "name": sys_obj.name, "stations": stations, "tick": sim.tick_count})


@app.route("/api/state")
def api_state():
    """Full universe state for frontend."""
    systems = {}
    for sid, sys in sim.universe.items():
        stations = []
        for st in sys.stations:
            sell_orders, buy_orders = _build_order_book(st)
            stations.append({
                "name": st.name,
                "station_type": st.station_type,
                "produces": st.produces,
                "production_rate": st.production_rate,
                "inventory": st.inventory,
                "prices": st.price_cache,
                "sell_orders": sell_orders,
                "buy_orders": buy_orders,
            })
        systems[sid] = {
            "name": sys.name,
            "type": sys.system_type,
            "cluster": sys.cluster,
            "security": sys.security,
            "faction": sys.faction,
            "x": sys.x, "y": sys.y, "z": sys.z,
            "stations": stations,
            "asteroid_fields": [{"name": a.name, "type": a.field_type, "yields": a.yields, "density": a.density} for a in sys.asteroid_fields],
            "connections": sys.connections,
            "objects": [{"id": o.id, "name": o.name, "type": o.obj_type, "distance": o.distance, "angle": round(o.angle, 4), "connects_to": o.connects_to, "parent": o.parent} for o in sys.objects],
        }
    return jsonify({"tick": sim.tick_count, "systems": systems})


@app.route("/api/ships")
def api_ships():
    """Ship positions and state for the game map."""
    since_tick = request.args.get('since_tick', type=int)
    tracker = supervisor.change_tracker if supervisor else None

    # Determine which ships to serialize
    changed_ids = None
    if since_tick is not None and tracker and tracker.has_tick(since_tick):
        changes = tracker.get_changes_since(since_tick)
        changed_ids = changes["ships"]

    ships = []
    for s in sim.ships:
        if changed_ids is not None and s.id not in changed_ids:
            continue
        ship_data = {
            "id": s.id, "name": s.name, "role": s.role, "ship_class": s.ship_class, "faction": s.faction,
            "state": s.state, "location": s.location, "destination": s.destination,
            "progress": round(s.progress, 4), "speed": s.speed, "cargo": s.cargo,
            "intra_position": s.intra_position, "intra_destination": s.intra_destination,
            "intra_progress": round(s.intra_progress, 4), "intra_speed": s.intra_speed,
        }
        # Include travel rate for client prediction
        if s.state == "traveling" and s.destination and s.location in sim.universe and s.destination in sim.universe:
            import math as _m
            _a = sim.universe[s.location]
            _b = sim.universe[s.destination]
            _dist = _m.sqrt((_a.x-_b.x)**2+(_a.y-_b.y)**2+(_a.z-_b.z)**2)
            _tt = max(3, min(15, _dist/70))
            ship_data["travel_rate"] = round(s.speed / _tt, 4)
        # Include origin/dest coordinates for client-side interpolation
        if s.state == "intra_traveling" and s.intra_position and s.intra_destination:
            from_obj = next((o for o in sim.universe[s.location].objects if o.id == s.intra_position), None)
            to_obj = next((o for o in sim.universe[s.location].objects if o.id == s.intra_destination), None)
            if from_obj and to_obj:
                import math
                dist = supervisor._intra_distance(s.location, s.intra_position, s.intra_destination)
                ship_data["intra_from"] = {"d": from_obj.distance, "a": round(from_obj.angle, 4)}
                ship_data["intra_to"] = {"d": to_obj.distance, "a": round(to_obj.angle, 4)}
                ship_data["intra_dist"] = round(dist, 3)
        ships.append(ship_data)
    return jsonify({"tick": sim.tick_count, "ships": ships, "delta": changed_ids is not None})


@app.route("/api/ship_model/<class_id>")
def api_ship_model(class_id):
    """Return 3D geometry data for a ship class."""
    from server.ship_geometry import get_ship_geometry, get_all_ship_geometries
    if class_id == "all":
        return jsonify(get_all_ship_geometries())
    geo = get_ship_geometry(class_id)
    if not geo:
        return jsonify({"error": "unknown ship class"}), 404
    return jsonify(geo)


@app.route("/api/debug")
def api_debug():
    """Pre-computed dashboard summary (~15KB). Updated every 10 ticks by dashboard worker."""
    # Find the dashboard worker's cache
    data = {}
    if supervisor:
        for w in supervisor.workers:
            if w.name == "dashboard":
                data = w.cache.data
                break
    if not data:
        return jsonify({"tick": 0, "error": "cache not ready"})

    # Inject live performance metrics and warfare status
    result = dict(data)
    if supervisor:
        result["performance"] = supervisor.metrics
        for w in supervisor.workers:
            if w.name == "battle_sim":
                result["warfare"] = w.get_status()
                break
    return jsonify(result)


@app.route("/api/system/<system_id>")
def api_system(system_id):
    """Detailed system view with objects and ship positions."""
    if system_id not in sim.universe:
        return jsonify({"error": "unknown system"}), 404

    since_tick = request.args.get('since_tick', type=int)
    tracker = supervisor.change_tracker if supervisor else None

    # If since_tick provided and system hasn't changed, return minimal response
    if since_tick is not None and tracker and tracker.has_tick(since_tick):
        changes = tracker.get_changes_since(since_tick)
        if system_id not in changes["systems"]:
            # Check if any ship in this system changed
            ship_changed = any(
                s.id in changes["ships"] for s in sim.ships if s.location == system_id
            )
            if not ship_changed:
                return jsonify({"tick": sim.tick_count, "changed": False})

    sys_obj = sim.universe[system_id]
    objects = [{"id": o.id, "name": o.name, "type": o.obj_type, "distance": o.distance, "angle": round(o.angle, 4), "connects_to": o.connects_to, "parent": o.parent} for o in sys_obj.objects]
    # Ships in this system
    ships_here = []
    for s in sim.ships:
        if s.location == system_id:
            ship_data = {
                "name": s.name, "role": s.role, "state": s.state,
                "ship_class": s.ship_class,
                "intra_position": s.intra_position, "intra_destination": s.intra_destination,
                "intra_progress": round(s.intra_progress, 4), "intra_speed": s.intra_speed,
            }
            if s.state == "intra_traveling" and s.intra_position and s.intra_destination:
                from_obj = next((o for o in sys_obj.objects if o.id == s.intra_position), None)
                to_obj = next((o for o in sys_obj.objects if o.id == s.intra_destination), None)
                if from_obj and to_obj:
                    dist = supervisor._intra_distance(system_id, s.intra_position, s.intra_destination)
                    ship_data["intra_from"] = {"d": from_obj.distance, "a": round(from_obj.angle, 4)}
                    ship_data["intra_to"] = {"d": to_obj.distance, "a": round(to_obj.angle, 4)}
                    ship_data["intra_dist"] = round(dist, 3)
            ships_here.append(ship_data)
    return jsonify({
        "id": system_id, "name": sys_obj.name, "type": sys_obj.system_type,
        "security": sys_obj.security, "objects": objects, "ships": ships_here,
        "tick": sim.tick_count, "changed": True,
    })


@app.route("/api/nuke", methods=["POST"])
def api_nuke():
    """Reset simulation to initial state."""
    global sim, supervisor
    supervisor.stop()
    clear_db()
    # Clear faction runtime data
    from server.game_data_db import get_data_db
    fconn = get_data_db()
    fconn.execute("DELETE FROM faction_decisions")
    fconn.execute("UPDATE corporations SET activity = NULL")
    fconn.execute("UPDATE build_projects SET accumulated = '{}', phase = 'scouting'")
    fconn.commit()
    fconn.close()
    sim = Simulation()
    supervisor = Supervisor(sim)
    supervisor.tick_rate = sim_speed["rate"]
    supervisor.multiplier = 1
    supervisor.add_worker(EconomyWorker(COMMODITIES, STATION_CONSUMPTION))
    supervisor.add_worker(NPCDecisionWorker(COMMODITIES))
    supervisor.add_worker(FactionStrategyWorker())
    supervisor.add_worker(BattleSimWorker())
    supervisor.add_worker(CorsairSpawnWorker())
    supervisor.add_worker(DashboardWorker(COMMODITIES, STATION_CONSUMPTION))
    supervisor.start()
    log.info("NUKE: Simulation reset to initial state")
    return jsonify({"status": "reset", "tick": sim.tick_count})


@app.route("/api/events")
def api_events():
    """Lightweight recent events endpoint."""
    return jsonify({"tick": sim.tick_count, "events": sim.events[-20:]})


@app.route("/api/speed", methods=["GET", "POST"])
def api_speed():
    """Get or set simulation speed multiplier. 1=realtime, 120=2hrs/min."""
    from flask import request
    if request.method == "POST":
        data = request.get_json(force=True)
        mult = max(1, min(120, int(data.get("multiplier", 1))))
        supervisor.multiplier = mult
        log.info(f"Sim speed set to {mult}x")
        return jsonify({"multiplier": mult})
    return jsonify({"multiplier": supervisor.multiplier})


# ── CRUD API for game data ────────────────────────────────────────────────────
@app.route("/api/reload_data", methods=["POST"])
def api_reload_data():
    """Reload game data from database without restarting server."""
    from server.data_access import is_db_ready, load_commodities, load_station_consumption
    if is_db_ready():
        import server.simulation as sim_mod
        sim_mod.COMMODITIES = load_commodities()
        sim_mod.STATION_CONSUMPTION = load_station_consumption()
        return jsonify({"status": "reloaded", "commodities": len(sim_mod.COMMODITIES)})
    return jsonify({"error": "database not ready"}), 500


@app.route("/api/data/commodities", methods=["GET"])
def api_data_commodities():
    """List all commodities from DB."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    rows = conn.execute("SELECT * FROM commodities ORDER BY tier, name").fetchall()
    result = []
    for r in rows:
        recipes = conn.execute("SELECT input_id, quantity FROM recipes WHERE commodity_id=?", (r["id"],)).fetchall()
        result.append({**dict(r), "stats": json.loads(r["stats"]), "recipe": {rec["input_id"]: rec["quantity"] for rec in recipes}})
    conn.close()
    return jsonify(result)


@app.route("/api/data/commodities/<commodity_id>", methods=["GET", "PUT"])
def api_data_commodity(commodity_id):
    """Get or update a single commodity."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    if request.method == "GET":
        row = conn.execute("SELECT * FROM commodities WHERE id=?", (commodity_id,)).fetchone()
        if not row:
            conn.close()
            return jsonify({"error": "not found"}), 404
        recipes = conn.execute("SELECT input_id, quantity FROM recipes WHERE commodity_id=?", (commodity_id,)).fetchall()
        conn.close()
        return jsonify({**dict(row), "stats": json.loads(row["stats"]), "recipe": {r["input_id"]: r["quantity"] for r in recipes}})
    else:
        data = request.get_json(force=True)
        conn.execute("""UPDATE commodities SET name=?, base_price=?, tier=?, volume=?, elasticity=?, description=?, stats=?
                       WHERE id=?""",
                    (data.get("name"), data.get("base_price"), data.get("tier"), data.get("volume"),
                     data.get("elasticity", 1.0), data.get("description", ""), json.dumps(data.get("stats", {})), commodity_id))
        # Update recipes
        if "recipe" in data:
            conn.execute("DELETE FROM recipes WHERE commodity_id=?", (commodity_id,))
            for inp_id, qty in data["recipe"].items():
                conn.execute("INSERT INTO recipes (commodity_id, input_id, quantity) VALUES (?,?,?)", (commodity_id, inp_id, qty))
        conn.commit()
        conn.close()
        return jsonify({"status": "updated", "id": commodity_id})


@app.route("/api/data/systems", methods=["GET"])
def api_data_systems():
    """List all systems from DB."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    rows = conn.execute("SELECT * FROM systems ORDER BY cluster, name").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/data/ships", methods=["GET"])
def api_data_ships():
    """List all ships (unified table)."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    rows = conn.execute("SELECT * FROM ships ORDER BY hull_class, tier, name").fetchall()
    conn.close()
    return jsonify([{**dict(r), "hardpoints": json.loads(r["hardpoints"]), "weapons": json.loads(r["weapons"]), "modules": json.loads(r["modules"]), "build_cost": json.loads(r["build_cost"])} for r in rows])


@app.route("/api/data/military_ships", methods=["GET"])
def api_data_military():
    """List faction military ships."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    rows = conn.execute("SELECT * FROM ships WHERE faction_id != '' ORDER BY faction_id, hull_class").fetchall()
    conn.close()
    return jsonify([{**dict(r), "hardpoints": json.loads(r["hardpoints"]), "weapons": json.loads(r["weapons"]), "modules": json.loads(r["modules"]), "build_cost": json.loads(r["build_cost"])} for r in rows])


@app.route("/api/data/ship_types", methods=["GET"])
def api_data_ship_types():
    """List non-faction ships (civilian hulls)."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    rows = conn.execute("SELECT * FROM ships WHERE faction_id = '' ORDER BY hull_class, tier").fetchall()
    conn.close()
    return jsonify([{**dict(r), "hardpoints": json.loads(r["hardpoints"]), "weapons": json.loads(r["weapons"]), "modules": json.loads(r["modules"]), "build_cost": json.loads(r["build_cost"])} for r in rows])


@app.route("/api/data/factions", methods=["GET"])
def api_data_factions():
    """List all factions from DB."""
    from server.data_access import load_factions
    return jsonify(load_factions())


@app.route("/api/data/faction_agents", methods=["GET"])
def api_data_faction_agents():
    """List all faction agents."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    rows = conn.execute("SELECT * FROM faction_agents WHERE alive=1 ORDER BY faction_id, role").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/data/faction_agents/regenerate", methods=["POST"])
def api_regenerate_agents():
    """Regenerate faction agents (all or single faction)."""
    from server.agent_generator import regenerate_all, regenerate_faction
    faction_id = request.args.get('faction', '')
    if faction_id:
        regenerate_faction(faction_id)
    else:
        regenerate_all()
    # Return fresh list
    from server.game_data_db import get_data_db
    conn = get_data_db()
    rows = conn.execute("SELECT * FROM faction_agents WHERE alive=1 ORDER BY faction_id, role").fetchall()
    conn.close()
    return jsonify({"status": "regenerated", "agents": [dict(r) for r in rows]})


if __name__ == "__main__":
    import webbrowser
    port = int(os.getenv("PORT", "8000"))
    if not os.getenv("FLY_APP_NAME") and not os.getenv("WERKZEUG_RUN_MAIN"):
        webbrowser.open(f"http://127.0.0.1:{port}")
    app.run(debug=True, host="0.0.0.0", port=port, threaded=True)
