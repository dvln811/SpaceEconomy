import os
import threading
import time
import logging
from flask import Flask, send_from_directory, jsonify, request, Response
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
    from server.workers.faction_events import FactionEventWorker
    supervisor.add_worker(FactionEventWorker())
    supervisor.add_worker(DashboardWorker(COMMODITIES, STATION_CONSUMPTION))
    supervisor.start()
    log.info(f"Supervisor started ({sim_speed['rate']}s/tick, {len(sim.ships)} NPCs, 7 workers)")
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


@app.route("/agents")
def agents_page():
    return send_from_directory(BASE_DIR, "agents.html")


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


_combat_state = {"paused": False, "stop": False}


@app.route("/combat")
def combat_page():
    return send_from_directory(BASE_DIR, "combat.html")


@app.route("/combat/stream")
def combat_stream():
    """Serve combat simulation as SSE stream."""
    import sys, math
    sys.path.insert(0, BASE_DIR)
    from combat_viewer import create_3faction_battle
    from server.combat_engine import CombatEngine
    import time as _time

    fleet_size = request.args.get('fleet_size', 22, type=int)
    fleet_size = max(4, min(1000, fleet_size))

    _combat_state["paused"] = False
    _combat_state["stop"] = False

    def generate():
        fleet_tf, fleet_fs, fleet_ic = create_3faction_battle(fleet_size)
        allied = fleet_tf + fleet_fs
        engine = CombatEngine(allied, fleet_ic)
        all_ships = allied + fleet_ic

        def ship_data(s):
            return {"id":s.id,"name":s.name,"hull_class":s.hull_class,
                    "geometry_id": getattr(s, 'geometry_id', s.id),
                    "shield":s.shield_max,"armor":s.armor_max,"hull":s.hull_max,
                    "cap":s.cap_max,"cap_recharge":s.cap_recharge,
                    "weapons":[{"name":w.name,"size":w.size,"dmg":w.damage_type.value,"cycle":w.cycle_time,"cap_use":w.cap_use,"ammo":w.ammo_id} for w in s.weapons],
                    "modules":[{"name":m.name,"type":m.slot} for m in s.modules],
                    "ammo":dict(s.ammo)}

        init_data = {"type":"init","fleets":[
            {"faction":"Terran Federation","count":len(fleet_tf),"ally":"Free States","ships":[ship_data(s) for s in fleet_tf]},
            {"faction":"Free States","count":len(fleet_fs),"ally":"Terran Federation","ships":[ship_data(s) for s in fleet_fs]},
            {"faction":"Iron Compact","count":len(fleet_ic),"ships":[ship_data(s) for s in fleet_ic]},
        ]}
        # Add a station to the battlefield for scale reference
        import random as _rnd
        station_types = ['trade_hub', 'military_base', 'refinery', 'mining_colony', 'shipyard', 'factory']
        st_type = _rnd.choice(station_types)
        st_faction = 'terran'
        st_path = os.path.join(BASE_DIR, "tools", "ship_designer", "station_designs", f"stations_{st_faction}_{st_type}.json")
        if os.path.exists(st_path):
            with open(st_path) as _sf:
                st_designs = json.load(_sf)
            st_design = _rnd.choice(st_designs)
            init_data["station"] = {"type": st_type, "faction": st_faction, "components": st_design["components"], "pos": [0, 0, 0]}
        yield f"data: {json.dumps(init_data)}\n\n"
        _time.sleep(1)

        while not engine.finished and engine.tick < 600 and not _combat_state["stop"]:
            while _combat_state["paused"] and not _combat_state["stop"]:
                _time.sleep(0.2)
            if _combat_state["stop"]:
                break

            events = engine.step()
            caps = {s.id: round(s.cap, 1) for s in all_ships if s.alive}
            positions = {s.id: [round(s.x), round(s.y), round(s.vx,2), round(s.vy,2), round(s.z), round(s.vz,2)] for s in all_ships if s.alive}
            msls = []
            for m in engine.missiles:
                target = next((s for s in all_ships if s.id == m.target_id and s.alive), None)
                if target:
                    dx = target.x - m.x; dy = target.y - m.y; dz = target.z - m.z
                    d = math.sqrt(dx*dx+dy*dy+dz*dz) or 1
                    msls.append({"x":round(m.x),"y":round(m.y),"z":round(m.z),"vx":round(dx/d*m.speed,1),"vy":round(dy/d*m.speed,1),"vz":round(dz/d*m.speed,1)})
                else:
                    msls.append({"x":round(m.x),"y":round(m.y),"z":round(m.z),"vx":0,"vy":0,"vz":0})
            tick_data = {'type':'tick','tick':engine.tick,'ship_caps':caps,'pos':positions,'msls':msls}
            # Batch events into tick message
            evts = []
            for e in events:
                evts.append({'tick':e.tick,'event':e.event,'source_id':e.source_id,'target_id':e.target_id,
                       'weapon':e.weapon,'damage':e.damage,'damage_type':e.damage_type,
                       'remaining_hp':e.remaining_hp,'detail':e.detail})
            tick_data['events'] = evts
            yield f"data: {json.dumps(tick_data)}\n\n"
            _time.sleep(1)
        result = engine.summary()
        yield f"data: {json.dumps({'type':'end','winner':result['winner'],'ticks':engine.tick})}\n\n"

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route("/ship_designer")
def ship_designer_page():
    return send_from_directory(os.path.join(BASE_DIR, "tools", "ship_designer"), "index.html")


@app.route("/combat/control")
def combat_control():
    cmd = request.args.get('cmd', '')
    if cmd == 'pause':
        _combat_state['paused'] = not _combat_state['paused']
    elif cmd == 'stop':
        _combat_state['stop'] = True
    elif cmd == 'restart':
        _combat_state['stop'] = True
    return "ok"


@app.route("/ship_designer/<path:filename>")
def ship_designer_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "tools", "ship_designer"), filename)


# ── Ship Designer API (proxied from tools/ship_designer/app.py) ──────────────
@app.route("/api/factions")
def api_designer_factions():
    import sys
    sys.path.insert(0, os.path.join(BASE_DIR, "tools", "ship_designer"))
    from ship_generator import FACTION_STYLES
    return jsonify({k: v["description"] for k, v in FACTION_STYLES.items()})


@app.route("/api/hull_classes")
def api_designer_hull_classes():
    import sys
    sys.path.insert(0, os.path.join(BASE_DIR, "tools", "ship_designer"))
    from ship_generator import HULL_CLASSES
    return jsonify(list(HULL_CLASSES.keys()))


@app.route("/api/generate", methods=["POST"])
def api_designer_generate():
    import sys
    sys.path.insert(0, os.path.join(BASE_DIR, "tools", "ship_designer"))
    from ship_generator import generate_ship
    params = request.get_json() or {}
    faction = params.get("faction", "terran")
    hull_class = params.get("hull_class", "frigate")
    seed = params.get("seed")
    if seed == "":
        seed = None
    elif seed:
        seed = int(seed)
    data = generate_ship(faction, hull_class, seed=seed)
    return jsonify(data)


@app.route("/api/station/types")
def api_station_types():
    import sys
    sys.path.insert(0, os.path.join(BASE_DIR, "tools", "ship_designer"))
    from station_generator import STATION_TYPES
    return jsonify(STATION_TYPES)


@app.route("/api/station/factions")
def api_station_factions():
    import sys
    sys.path.insert(0, os.path.join(BASE_DIR, "tools", "ship_designer"))
    from station_generator import STATION_FACTION_STYLES
    return jsonify({k: v['description'] for k, v in STATION_FACTION_STYLES.items()})


@app.route("/api/station/generate", methods=["POST"])
def api_station_generate():
    import sys
    sys.path.insert(0, os.path.join(BASE_DIR, "tools", "ship_designer"))
    from station_generator import generate_station
    params = request.get_json() or {}
    station_type = params.get("station_type", "trade_hub")
    faction = params.get("faction", "terran")
    seed = params.get("seed")
    if seed == "" or seed is None:
        seed = None
    else:
        seed = int(seed)
    data = generate_station(station_type, faction, seed=seed)
    return jsonify(data)


@app.route("/api/station/batch", methods=["POST"])
def api_station_batch():
    """Generate 1 station per type per faction for review."""
    import sys
    sys.path.insert(0, os.path.join(BASE_DIR, "tools", "ship_designer"))
    from station_generator import generate_station, STATION_TYPES, STATION_FACTION_STYLES
    import random as _rnd
    params = request.get_json() or {}
    station_type = params.get("station_type", "trade_hub")
    results = []
    for faction in STATION_FACTION_STYLES:
        seed = _rnd.randint(0, 999999)
        data = generate_station(station_type, faction, seed=seed)
        results.append({"name": f"{faction}/{station_type}/{seed}", "faction": faction,
                        "station_type": station_type, "seed": seed,
                        "components": data["components"], "meta": data["meta"]})
    return jsonify(results)


@app.route("/api/saved")
def api_designer_saved():
    save_dir = os.path.join(BASE_DIR, "tools", "ship_designer", "saved_designs")
    os.makedirs(save_dir, exist_ok=True)
    files = [f[:-5] for f in os.listdir(save_dir) if f.endswith(".json")]
    return jsonify(files)


@app.route("/api/save", methods=["POST"])
def api_designer_save():
    data = request.get_json()
    name = data.get("name", "unnamed")
    safe_name = "".join(c for c in name if c.isalnum() or c in "_-").lower()
    save_dir = os.path.join(BASE_DIR, "tools", "ship_designer", "saved_designs")
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f"{safe_name}.json")
    with open(path, "w") as f:
        json.dump(data["design"], f, indent=2)
    return jsonify({"status": "saved"})


@app.route("/api/load/<name>")
def api_designer_load(name):
    path = os.path.join(BASE_DIR, "tools", "ship_designer", "saved_designs", f"{name}.json")
    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 404
    with open(path) as f:
        return jsonify(json.load(f))


@app.route("/api/batch_generate", methods=["POST"])
def api_designer_batch():
    import sys, random as _rnd
    sys.path.insert(0, os.path.join(BASE_DIR, "tools", "ship_designer"))
    from ship_generator import generate_ship
    params = request.get_json() or {}
    hull_class = params.get("hull_class", "fighter")
    count = int(params.get("count", 4))
    factions = ["terran", "merchants", "science", "iron_compact", "frontier"]
    results = []
    for faction in factions:
        for i in range(count):
            seed = _rnd.randint(0, 999999)
            ship = generate_ship(faction=faction, hull_class=hull_class, seed=seed)
            results.append({"name": f"{faction}/{hull_class}/{seed}", "faction": faction,
                            "hull_class": hull_class, "seed": seed,
                            "components": ship["components"], "meta": ship["meta"]})
    return jsonify(results)


@app.route("/api/all_components")
def api_designer_all_components():
    import sys
    sys.path.insert(0, os.path.join(BASE_DIR, "tools", "ship_designer"))
    from component_library import GENERATORS
    comp_dir = os.path.join(BASE_DIR, "tools", "ship_designer", "saved_components")
    items = []
    for cat, (fn, styles) in GENERATORS.items():
        for style in styles:
            result = fn(style=style, size=1.0, seed=42)
            items.append({"name": f"{cat}/{style}", "category": cat, "parts": result["parts"]})
    for fname in sorted(os.listdir(comp_dir)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(comp_dir, fname)) as f:
            data = json.load(f)
        items.append({"name": fname[:-5], "category": data.get("category", "other"), "parts": data["parts"]})
    return jsonify(items)


@app.route("/api/component_categories")
def api_designer_comp_categories():
    import sys
    sys.path.insert(0, os.path.join(BASE_DIR, "tools", "ship_designer"))
    from component_library import GENERATORS, COMPONENT_CATEGORIES
    return jsonify({k: {"description": COMPONENT_CATEGORIES[k], "styles": styles}
                    for k, (_, styles) in GENERATORS.items()})


@app.route("/api/generate_component", methods=["POST"])
def api_designer_gen_component():
    import sys
    sys.path.insert(0, os.path.join(BASE_DIR, "tools", "ship_designer"))
    from component_library import generate_component
    params = request.get_json() or {}
    category = params.get("category", "cockpit")
    style = params.get("style")
    size = float(params.get("size", 1.0))
    seed = params.get("seed")
    if seed == "" or seed is None:
        seed = None
    else:
        seed = int(seed)
    return jsonify(generate_component(category=category, style=style, size=size, seed=seed))


@app.route("/api/export_tagged", methods=["POST"])
def api_designer_export_tagged():
    data = request.get_json()
    filename = data.get('filename', 'tagged_feedback') if isinstance(data, dict) else 'tagged_feedback'
    items = data.get('items', data) if isinstance(data, dict) else data
    safe_name = "".join(c for c in filename if c.isalnum() or c in "_-").lower()
    path = os.path.join(BASE_DIR, "tools", "ship_designer", f"{safe_name}.json")
    with open(path, "w") as f:
        json.dump(items, f, indent=2)
    return jsonify({"status": "saved", "count": len(items), "file": f"{safe_name}.json"})


@app.route("/api/save_component", methods=["POST"])
def api_designer_save_component():
    data = request.get_json()
    name = data.get("name", "unnamed")
    safe_name = "".join(c for c in name if c.isalnum() or c in "_-").lower()
    comp_dir = os.path.join(BASE_DIR, "tools", "ship_designer", "saved_components")
    os.makedirs(comp_dir, exist_ok=True)
    with open(os.path.join(comp_dir, f"{safe_name}.json"), "w") as f:
        json.dump(data["component"], f, indent=2)
    return jsonify({"status": "saved"})


@app.route("/api/saved_components")
def api_designer_saved_components():
    comp_dir = os.path.join(BASE_DIR, "tools", "ship_designer", "saved_components")
    os.makedirs(comp_dir, exist_ok=True)
    files = [f[:-5] for f in os.listdir(comp_dir) if f.endswith(".json")]
    return jsonify(files)


@app.route("/api/load_component/<name>")
def api_designer_load_component(name):
    path = os.path.join(BASE_DIR, "tools", "ship_designer", "saved_components", f"{name}.json")
    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 404
    with open(path) as f:
        return jsonify(json.load(f))


@app.route("/api/station_designs/<faction>/<station_type>")
def api_station_designs(faction, station_type):
    """Get pre-generated station designs for a faction+type (6 variants)."""
    path = os.path.join(BASE_DIR, "tools", "ship_designer", "station_designs", f"stations_{faction}_{station_type}.json")
    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 404
    with open(path) as f:
        return jsonify(json.load(f))


@app.route("/api/station_model/<station_id>")
def api_station_model(station_id):
    """Get the 3D model components for a specific station."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    row = conn.execute("""SELECT s.station_type, s.geometry_variant, sys.faction_id
                          FROM stations s JOIN systems sys ON s.system_id = sys.id
                          WHERE s.id=?""", (station_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "station not found"}), 404
    faction_map = {'terran_fed':'terran','science_collective':'science','merchants_guild':'merchants',
                   'free_states':'frontier','iron_compact':'iron_compact','corsairs':'frontier','':'frontier'}
    design_faction = faction_map.get(row['faction_id'], 'frontier')
    variant = row['geometry_variant'] or 0
    path = os.path.join(BASE_DIR, "tools", "ship_designer", "station_designs",
                        f"stations_{design_faction}_{row['station_type']}.json")
    if not os.path.exists(path):
        return jsonify({"error": "no design file"}), 404
    with open(path) as f:
        designs = json.load(f)
    idx = variant % len(designs)
    return jsonify(designs[idx])


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
    # Designer endpoints don't need sim
    exempt = ('/api/factions', '/api/hull_classes', '/api/generate', '/api/station/',
              '/api/batch_generate', '/api/saved', '/api/save', '/api/load/',
              '/api/all_components', '/api/component_categories', '/api/generate_component',
              '/api/save_component', '/api/saved_components', '/api/load_component/',
              '/api/export_tagged', '/api/ship_model/', '/api/agents', '/api/data/',
              '/api/station_designs/', '/api/station_model/', '/api/player')
    if request.path.startswith('/api/') and not _sim_ready.is_set():
        if not any(request.path.startswith(p) for p in exempt):
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
    from server.simulation import COMMODITIES as COMS
    from server.game_data_db import get_data_db
    region_filter = request.args.get('region', '')
    buy_orders = []
    sell_orders = []

    # Build item category sets once
    if not hasattr(api_market_orders, '_mil_items'):
        conn = get_data_db()
        api_market_orders._mil_items = [r[0] for r in conn.execute(
            "SELECT id FROM commodities WHERE category IN ('Weapons','Ammunition','Drones','Ship Equipment')").fetchall()]
        api_market_orders._civ_items = [r[0] for r in conn.execute(
            "SELECT id FROM commodities WHERE category IN ('Weapons','Ammunition','Drones','Ship Equipment','Materials','Trade Goods')").fetchall()]
        conn.close()
    MILITARY_ITEMS = api_market_orders._mil_items
    CIVILIAN_ITEMS = api_market_orders._civ_items

    for sid, sys_obj in sim.universe.items():
        region = getattr(sys_obj, 'region', '')
        if region_filter and region != region_filter:
            continue
        # Station-based orders (production needs + consumption)
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

            # Military base demand for combat items
            if st.station_type == 'military_base':
                import random as _rnd
                for item_id in _rnd.sample(MILITARY_ITEMS, min(20, len(MILITARY_ITEMS))):
                    if item_id in COMS:
                        buy_orders.append({'commodity': item_id, 'qty': _rnd.randint(10, 200),
                            'price': round(COMS[item_id].base_price * 1.3, 2),
                            'station': st.name, 'system': sys_obj.name, 'system_id': sid, 'region': region})

            # Refineries always buy ALL raw ores including exotics
            if st.station_type == 'refinery':
                RARE_ORES = ['gold_ore','platinum_ore','palladium_ore','tungsten_ore',
                             'helium3','xenon_gas','quartz_crystal','lithium_crystal',
                             'beryllium_crystal','kraxolite','void_shard','neutronium']
                for ore_id in RARE_ORES:
                    if ore_id in COMS:
                        buy_orders.append({'commodity': ore_id, 'qty': 200,
                            'price': round(COMS[ore_id].base_price * 1.2, 2),
                            'station': st.name, 'system': sys_obj.name, 'system_id': sid, 'region': region})

            # Shipyards buy exotic materials for capital construction
            if st.station_type == 'shipyard':
                SHIPYARD_NEEDS = ['gold_ore','platinum_ore','palladium_ore','neutronium',
                                  'kraxolite','void_shard','titanium_ore','tungsten_ore']
                for mat_id in SHIPYARD_NEEDS:
                    if mat_id in COMS:
                        buy_orders.append({'commodity': mat_id, 'qty': 500,
                            'price': round(COMS[mat_id].base_price * 1.5, 2),
                            'station': st.name, 'system': sys_obj.name, 'system_id': sid, 'region': region})

        # Civilian population demand
        pop = getattr(sys_obj, 'population', 0) or 0
        if pop > 10000:
            import random as _rnd
            demand_scale = min(50, max(1, pop // 500000))
            # All stations in populated systems generate some civilian demand
            for st in sys_obj.stations:
                n_items = min(20, max(5, demand_scale))
                for item_id in _rnd.sample(CIVILIAN_ITEMS, min(n_items, len(CIVILIAN_ITEMS))):
                    if item_id in COMS:
                        qty = max(1, demand_scale * _rnd.randint(1, 5))
                        buy_orders.append({'commodity': item_id, 'qty': qty,
                            'price': round(COMS[item_id].base_price * 0.8, 2),
                            'station': st.name, 'system': sys_obj.name, 'system_id': sid, 'region': region})

    # Include build project demand
    global _project_orders_cache, _project_orders_tick
    if sim.tick_count - _project_orders_tick > 60:
        _project_orders_cache = _get_project_buy_orders()
        _project_orders_tick = sim.tick_count
    for sys_id, proj_orders in _project_orders_cache.items():
        sys_obj = sim.universe.get(sys_id)
        if not sys_obj:
            continue
        region = getattr(sys_obj, 'region', '')
        if region_filter and region != region_filter:
            continue
        for o in proj_orders:
            o['system'] = sys_obj.name
            o['system_id'] = sys_id
            o['region'] = region
            o['station'] = 'Build Project'
            buy_orders.append(o)

    return jsonify({"tick": sim.tick_count, "region": region_filter,
                    "buy_orders": buy_orders[:1000],
                    "sell_orders": sell_orders[:1000]})


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


@app.route("/api/news")
def api_news():
    """Return last 75 news/event log entries, filtering out stubs."""
    if not sim:
        return jsonify([])
    HIDE_PREFIXES = ('QUEUE:', 'BUILT:', 'TRADE:')
    all_events = sim.events if hasattr(sim, 'events') else []
    filtered = [e for e in all_events if not any(e.get('msg', '').startswith(p) for p in HIDE_PREFIXES) and e.get('category') != 'price']
    events = filtered[-75:]
    return jsonify(list(reversed(events)))


@app.route("/api/prices/ticker")
def api_prices_ticker():
    """Return last 30 price change messages for the scrolling ticker."""
    if not sim:
        return jsonify([])
    all_events = sim.events if hasattr(sim, 'events') else []
    prices = [e for e in all_events if e.get('category') == 'price']
    return jsonify(prices[-30:])


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
    objects = [{"id": o.id, "name": o.name, "type": o.obj_type, "distance": o.distance, "angle": round(o.angle, 4), "connects_to": o.connects_to, "parent": o.parent, "station_id": getattr(o, 'station_id', '')} for o in sys_obj.objects]
    # Ships in this system
    ships_here = []
    for s in sim.ships:
        if s.location == system_id:
            ship_data = {
                "name": s.name, "role": s.role, "state": s.state,
                "ship_class": s.ship_class, "speed": s.speed,
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


@app.route("/api/agents")
def api_agents():
    """Browse agents with optional filters: faction, role, alive, system."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    sql = "SELECT * FROM faction_agents WHERE 1=1"
    params = []
    faction = request.args.get('faction')
    role = request.args.get('role')
    alive = request.args.get('alive')
    system = request.args.get('system')
    if faction:
        sql += " AND faction_id=?"
        params.append(faction)
    if role:
        sql += " AND role=?"
        params.append(role)
    if alive is not None:
        sql += " AND alive=?"
        params.append(int(alive))
    if system:
        sql += " AND system_id=?"
        params.append(system)
    sql += " ORDER BY faction_id, rank DESC, name"
    rows = conn.execute(sql, params).fetchall()
    # Attach history for each agent
    agents = []
    for r in rows:
        a = dict(r)
        hist = conn.execute("SELECT tick, event_type, detail FROM agent_history WHERE agent_id=? ORDER BY tick DESC LIMIT 10",
                            (a['id'],)).fetchall()
        a['history'] = [dict(h) for h in hist]
        agents.append(a)
    conn.close()
    return jsonify(agents)


@app.route("/api/agents/<agent_id>")
def api_agent_detail(agent_id):
    """Get single agent with full history and family."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    row = conn.execute("SELECT * FROM faction_agents WHERE id=?", (agent_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "not found"}), 404
    agent = dict(row)
    agent['history'] = [dict(h) for h in conn.execute(
        "SELECT tick, event_type, detail, related_agent_id, system_id FROM agent_history WHERE agent_id=? ORDER BY tick DESC",
        (agent_id,)).fetchall()]
    # Family: spouse, parent, children, clan members
    if agent.get('spouse_id'):
        s = conn.execute("SELECT id, name, title, role, alive FROM faction_agents WHERE id=?", (agent['spouse_id'],)).fetchone()
        agent['spouse'] = dict(s) if s else None
    if agent.get('parent_id'):
        p = conn.execute("SELECT id, name, title, role, alive FROM faction_agents WHERE id=?", (agent['parent_id'],)).fetchone()
        agent['parent'] = dict(p) if p else None
    agent['children'] = [dict(c) for c in conn.execute(
        "SELECT id, name, title, role, alive FROM faction_agents WHERE parent_id=?", (agent_id,)).fetchall()]
    agent['clan_members'] = [dict(c) for c in conn.execute(
        "SELECT id, name, title, role, alive, age FROM faction_agents WHERE clan=? AND faction_id=? AND id!=? ORDER BY age DESC",
        (agent.get('clan',''), agent.get('faction_id',''), agent_id)).fetchall()]
    conn.close()
    return jsonify(agent)


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


# ── Player API ─────────────────────────────────────────────────────────────────

# Local Space Worker (persistent 3D simulation of player's system)
from server.local_space import LocalSpaceWorker
local_space = LocalSpaceWorker()
local_space.start()


def _init_local_space():
    """Initialize local space for player's current system after sim loads."""
    from server.game_data_db import get_data_db
    if not _sim_ready.wait(120):
        return
    conn = get_data_db()
    p = conn.execute("SELECT system_id, ship_class, station_id, intra_position FROM player WHERE id='player1'").fetchone()
    conn.close()
    if not p or not p['system_id']:
        return
    sys_obj = sim.universe.get(p['system_id'])
    if not sys_obj:
        return
    # Load system objects into local space
    local_space.load_system(p['system_id'], sys_obj.objects,
                            [s for s in sim.ships if s.location == p['system_id']])
    # Place player
    conn2 = get_data_db()
    ship_row = conn2.execute("SELECT speed FROM ships WHERE id=?", (p['ship_class'],)).fetchone()
    conn2.close()
    speed = ship_row['speed'] if ship_row else 100
    pos_id = p['intra_position'] or ''
    local_space.set_player_ship('player1', p['ship_class'], speed, pos_id)
    log.info(f"LocalSpace loaded: system={p['system_id']}, {len(local_space.objects)} objects, {len(local_space.ships)} ships")

threading.Thread(target=_init_local_space, daemon=True).start()


@app.route("/api/player/local_space/reload", methods=["POST"])
def api_reload_local_space():
    """Force reload local space (for debugging)."""
    threading.Thread(target=_init_local_space, daemon=True).start()
    return jsonify({"status": "reloading"})


@app.route("/api/player/local_space")
def api_player_local_space():
    """Return full local space state."""
    return jsonify(local_space.get_state())


@app.route("/api/player/local_space/stream")
def api_player_local_space_stream():
    """Stream local space state as SSE, one tick per second."""
    def generate():
        while True:
            state = local_space.get_state()
            yield f"data: {json.dumps(state)}\n\n"
            time.sleep(1)

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route("/api/player/fly", methods=["POST"])
def api_player_fly():
    """Set player flight direction."""
    data = request.get_json() or {}
    dx = float(data.get('dx', 0))
    dy = float(data.get('dy', 0))
    dz = float(data.get('dz', 0))
    local_space.player_fly(dx, dy, dz)
    return jsonify({"status": "flying"})


@app.route("/api/player/stop", methods=["POST"])
def api_player_stop():
    """Stop player ship."""
    local_space.player_stop()
    return jsonify({"status": "stopping"})


@app.route("/api/player/position", methods=["POST"])
def api_player_position():
    """Client reports player ship position (client-authoritative for local movement)."""
    data = request.get_json() or {}
    with local_space._lock:
        if local_space.player_ship:
            local_space.player_ship.x = float(data.get('x', 0))
            local_space.player_ship.y = float(data.get('y', 0))
            local_space.player_ship.z = float(data.get('z', 0))
            local_space.player_ship.speed = float(data.get('speed', 0))
            local_space.player_ship.heading_x = float(data.get('hx', 1))
            local_space.player_ship.heading_y = float(data.get('hy', 0))
            local_space.player_ship.heading_z = float(data.get('hz', 0))
            local_space.player_ship.state = data.get('state', 'idle')
    return jsonify({"status": "ok"})

@app.route("/api/player")
def api_player():
    """Get player state. Also advances warp if in progress."""
    from server.game_data_db import get_data_db
    import math
    conn = get_data_db()
    row = conn.execute("SELECT * FROM player WHERE id='player1'").fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "no player"}), 404
    p = dict(row)

    # Advance warp if warping
    if p['state'] == 'warping' and p['intra_destination']:
        # Get ship speed
        ship_row = conn.execute("SELECT speed FROM ships WHERE id=?", (p['ship_class'],)).fetchone()
        ship_speed = ship_row['speed'] if ship_row else 200
        # Get distance
        from_obj = conn.execute("SELECT distance, angle FROM system_objects WHERE id=? AND system_id=?",
                                (p['intra_position'], p['system_id'])).fetchone()
        to_obj = conn.execute("SELECT distance, angle FROM system_objects WHERE id=? AND system_id=?",
                              (p['intra_destination'], p['system_id'])).fetchone()
        if from_obj and to_obj:
            ax = from_obj['distance'] * math.cos(from_obj['angle'])
            ay = from_obj['distance'] * math.sin(from_obj['angle'])
            bx = to_obj['distance'] * math.cos(to_obj['angle'])
            by = to_obj['distance'] * math.sin(to_obj['angle'])
            dist = max(0.5, math.sqrt((ax-bx)**2 + (ay-by)**2))
            warp_speed = ship_speed * 0.0015
            travel_ticks = max(5, dist / warp_speed)
            step = 1.0 / travel_ticks
            new_progress = p['intra_progress'] + step
            if new_progress >= 1.0:
                # Arrived
                conn.execute("UPDATE player SET state='idle', intra_position=?, intra_destination='', intra_progress=0 WHERE id='player1'",
                             (p['intra_destination'],))
                p['state'] = 'idle'
                p['intra_position'] = p['intra_destination']
                p['intra_destination'] = ''
                p['intra_progress'] = 0
            else:
                conn.execute("UPDATE player SET intra_progress=? WHERE id='player1'", (new_progress,))
                p['intra_progress'] = new_progress
        conn.commit()

    p['cargo'] = json.loads(p.get('cargo') or '{}')
    p['fittings'] = json.loads(p.get('fittings') or '{}')
    conn2 = get_data_db()
    ship_row = conn2.execute("SELECT * FROM ships WHERE id=?", (p['ship_class'],)).fetchone()
    sys_row = conn2.execute("SELECT name, sec_level, faction_id FROM systems WHERE id=?", (p['system_id'],)).fetchone()
    st_row = conn2.execute("SELECT name, station_type FROM stations WHERE id=?", (p['station_id'],)).fetchone() if p.get('station_id') else None
    conn2.close()
    conn.close()
    if ship_row:
        p['ship_stats'] = dict(ship_row)
    if sys_row:
        p['system_name'] = sys_row['name']
        p['system_sec'] = sys_row['sec_level']
    if st_row:
        p['station_name'] = st_row['name']
        p['station_type'] = st_row['station_type']
    return jsonify(p)


@app.route("/api/player/undock", methods=["POST"])
def api_player_undock():
    """Undock player from station."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    p = conn.execute("SELECT * FROM player WHERE id='player1'").fetchone()
    if not p or not p['docked']:
        conn.close()
        return jsonify({"error": "not docked"}), 400
    # Find the station's system object to set intra_position
    st_obj = conn.execute("SELECT id FROM system_objects WHERE station_id=? LIMIT 1", (p['station_id'],)).fetchone()
    intra_pos = st_obj['id'] if st_obj else ''
    conn.execute("UPDATE player SET docked=0, state='idle', intra_position=? WHERE id='player1'", (intra_pos,))
    conn.commit()
    conn.close()
    return jsonify({"status": "undocked", "intra_position": intra_pos})


@app.route("/api/player/dock", methods=["POST"])
def api_player_dock():
    """Dock player at nearest station."""
    from server.game_data_db import get_data_db
    conn = get_data_db()
    p = conn.execute("SELECT * FROM player WHERE id='player1'").fetchone()
    if not p or p['docked']:
        conn.close()
        return jsonify({"error": "already docked"}), 400
    # Find what station we're at (intra_position must be a station object)
    obj = conn.execute("SELECT station_id FROM system_objects WHERE id=? AND obj_type='station'", (p['intra_position'],)).fetchone()
    if not obj or not obj['station_id']:
        conn.close()
        return jsonify({"error": "not at a station"}), 400
    conn.execute("UPDATE player SET docked=1, state='docked', station_id=?, intra_destination='', intra_progress=0 WHERE id='player1'", (obj['station_id'],))
    conn.commit()
    conn.close()
    return jsonify({"status": "docked", "station_id": obj['station_id']})


@app.route("/api/player/warp", methods=["POST"])
def api_player_warp():
    """Start warp to a system object (via local space worker)."""
    data = request.get_json() or {}
    target_obj_id = data.get('target')
    if not target_obj_id:
        return jsonify({"error": "no target"}), 400
    local_space.player_warp(target_obj_id)
    return jsonify({"status": "warping", "target": target_obj_id})


if __name__ == "__main__":
    import webbrowser
    port = int(os.getenv("PORT", "8000"))
    if not os.getenv("FLY_APP_NAME") and not os.getenv("WERKZEUG_RUN_MAIN"):
        webbrowser.open(f"http://127.0.0.1:{port}")
    app.run(debug=True, host="0.0.0.0", port=port, threaded=True)
