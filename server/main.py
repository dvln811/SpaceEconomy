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
        if qty > 1:
            price = st.price_cache.get(commodity_id, 0)
            if price > 0:
                sell_orders.append({"commodity": commodity_id, "qty": round(qty, 1), "price": round(price, 1)})
    for prod_id in st.produces:
        com = COMS.get(prod_id)
        if not com or not com.recipe:
            continue
        for inp_id, qty_needed in com.recipe.items():
            want = qty_needed * st.production_rate * 100
            have = st.inventory.get(inp_id, 0)
            deficit = want - have
            if deficit > 0:
                base = st.price_cache.get(inp_id, 0)
                buy_price = base * 1.1 if base > 0 else COMS[inp_id].base_price * 1.1 if inp_id in COMS else 0
                if buy_price > 0:
                    buy_orders.append({"commodity": inp_id, "qty": round(deficit, 1), "price": round(buy_price, 1)})
    for commodity_id in STATION_CONSUMPTION.get(st.station_type, []):
        have = st.inventory.get(commodity_id, 0)
        if have < 500:
            base = st.price_cache.get(commodity_id, 0)
            buy_price = base * 1.15 if base > 0 else COMS[commodity_id].base_price * 1.15 if commodity_id in COMS else 0
            if buy_price > 0:
                buy_orders.append({"commodity": commodity_id, "qty": round(500 - have, 1), "price": round(buy_price, 1)})
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
                # Direct demand for the component/material
                price = COMS[mat_id].base_price * 1.2 if mat_id in COMS else 1000
                orders_by_system[target].append({"commodity": mat_id, "qty": round(deficit), "price": round(price, 1)})
                # Also cascade: post demand for recipe inputs of this material
                com = COMS.get(mat_id)
                if com and com.recipe:
                    for inp_id, inp_qty in com.recipe.items():
                        inp_need = inp_qty * deficit
                        inp_price = COMS[inp_id].base_price * 1.15 if inp_id in COMS else 100
                        orders_by_system[target].append({"commodity": inp_id, "qty": round(inp_need), "price": round(inp_price, 1)})
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


@app.route("/economy")
def economy_page():
    return send_from_directory(BASE_DIR, "economy.html")


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


@app.route("/factions")
def factions_page():
    return send_from_directory(BASE_DIR, "factions_doc.html")


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
            "security": sys.security, "faction": sys.faction,
            "region": getattr(sys, 'region', ''),
            "x": sys.x, "y": sys.y, "z": sys.z,
            "connections": sys.connections,
            "station_count": len(sys.stations),
            "has_asteroids": len(sys.asteroid_fields) > 0,
        }
    return jsonify({"systems": systems})


@app.route("/api/market/ships")
def api_market_ships():
    """Ships available at shipyard stations with computed prices."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    rows = conn.execute("SELECT id, name, hull_class, build_cost, build_time FROM ships ORDER BY hull_class, name").fetchall()
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
    """Debug summary for the monitor page."""
    from server.simulation import COMMODITIES as COMS
    summary = sim.get_state_summary()

    since_tick = request.args.get('since_tick', type=int)
    tracker = supervisor.change_tracker if supervisor else None
    is_delta = since_tick is not None and tracker and tracker.has_tick(since_tick)
    changes = tracker.get_changes_since(since_tick) if is_delta else None

    # Per-system station production details
    systems_detail = {}
    for sid, sys_obj in sim.universe.items():
        if is_delta and sid not in changes["systems"]:
            continue
        stations_info = []
        for st in sys_obj.stations:
            # Calculate production health for each output
            prod_status = []
            for prod_id in st.produces:
                com = COMS.get(prod_id)
                if not com or not com.recipe:
                    continue
                # How much can we produce right now?
                can_produce = st.production_rate
                inputs_status = []
                for inp_id, qty_needed in com.recipe.items():
                    avail = st.inventory.get(inp_id, 0)
                    possible = avail / qty_needed if qty_needed > 0 else 999
                    can_produce = min(can_produce, possible)
                    inputs_status.append({"id": inp_id, "name": COMS[inp_id].name, "need": qty_needed * st.production_rate, "have": round(avail, 1)})
                prod_status.append({
                    "output": prod_id, "name": com.name,
                    "rate": st.production_rate, "actual": round(min(can_produce, st.production_rate), 2),
                    "halted": can_produce <= 0, "inputs": inputs_status,
                    "stock": round(st.inventory.get(prod_id, 0), 1),
                })
            # Get project buy orders for this system
            global _project_orders_cache, _project_orders_tick
            if sim.tick_count - _project_orders_tick > 60:
                _project_orders_cache = _get_project_buy_orders()
                _project_orders_tick = sim.tick_count
            proj_orders = _project_orders_cache.get(sid, [])
            stations_info.append({
                "name": st.name, "type": st.station_type,
                "production": prod_status,
                "inventory": {k: round(v, 1) for k, v in st.inventory.items() if v > 0.1},
                "sell_orders": _build_order_book(st)[0][:10],
                "buy_orders": (_build_order_book(st)[1] + proj_orders)[:20],
            })
        ships_in_sys = sum(1 for s in sim.ships if s.location == sid)
        systems_detail[sid] = {
            "name": sys_obj.name, "cluster": sys_obj.cluster, "security": sys_obj.security,
            "faction": sys_obj.faction, "region": getattr(sys_obj, 'region', ''),
            "type": sys_obj.system_type, "stations": stations_info, "ships_count": ships_in_sys,
            "connections": sys_obj.connections,
            "belts": [{"name": b.name, "yields": b.yields, "density": b.density} for b in sys_obj.asteroid_fields],
        }
    summary["systems"] = systems_detail

    # Price data (top entries per commodity)
    prices = {}
    for sid, sys_obj in sim.universe.items():
        for st in sys_obj.stations:
            for commodity, price in st.price_cache.items():
                if st.inventory.get(commodity, 0) > 0.1:
                    prices.setdefault(commodity, []).append({"system": sys_obj.name, "system_id": sid, "station": st.name, "price": round(price, 1), "stock": round(st.inventory.get(commodity, 0), 1)})
    summary["prices"] = prices

    # Ship details with full info
    ships = []
    for s in sim.ships:
        if is_delta and s.id not in changes["ships"]:
            continue
        loc_name = sim.universe[s.location].name if s.location in sim.universe else s.location or "-"
        dest_name = sim.universe[s.destination].name if s.destination in sim.universe else s.destination or "-"
        ships.append({
            "id": s.id, "name": s.name, "state": s.state, "role": s.role,
            "ship_class": s.ship_class, "faction": s.faction, "timer": s.state_timer,
            "location": loc_name, "location_id": s.location,
            "destination": dest_name, "destination_id": s.destination,
            "cargo": s.cargo, "cargo_capacity": s.cargo_capacity,
            "cargo_used": round(sum(s.cargo.values()), 1),
            "progress": round(s.progress, 3),
            "risk_tolerance": s.risk_tolerance,
            "route_path": [sim.universe[r].name for r in s.route_path if r in sim.universe],
            "intra_position": s.intra_position, "intra_destination": s.intra_destination,
            "intra_progress": round(s.intra_progress, 3),
        })
    summary["ships"] = ships

    # Demand data: what the economy needs vs what it has
    demand_data = {}
    for sid, sys_obj in sim.universe.items():
        for st in sys_obj.stations:
            for prod_id in st.produces:
                com = COMS.get(prod_id)
                if not com or not com.recipe:
                    continue
                for inp_id, qty_needed in com.recipe.items():
                    demand_data.setdefault(inp_id, {"demand_per_tick": 0, "total_supply": 0, "name": COMS[inp_id].name})
                    demand_data[inp_id]["demand_per_tick"] += qty_needed * st.production_rate
    # Add supply totals
    for sid, sys_obj in sim.universe.items():
        for st in sys_obj.stations:
            for commodity, qty in st.inventory.items():
                if commodity in demand_data:
                    demand_data[commodity]["total_supply"] += qty
    # Calculate deficit (how many ticks of supply remain)
    for k, v in demand_data.items():
        v["ticks_remaining"] = round(v["total_supply"] / v["demand_per_tick"], 1) if v["demand_per_tick"] > 0 else 9999
        v["deficit"] = round(v["demand_per_tick"] * 100 - v["total_supply"], 1)  # shortfall for 100 ticks
    summary["demand"] = demand_data
    # Get warfare status from battle worker
    warfare_status = {"fleet_strength": {}, "ships_destroyed": 0, "ships_built": 0}
    if supervisor:
        for w in supervisor.workers:
            if w.name == "battle_sim":
                warfare_status = w.get_status()
                break
    summary["warfare"] = warfare_status

    # Performance metrics from supervisor
    if supervisor:
        summary["performance"] = supervisor.metrics

    summary["delta"] = is_delta
    return jsonify(summary)


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
