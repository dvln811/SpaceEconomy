import os
import threading
import time
import logging
from flask import Flask, send_from_directory, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("space_economy")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder=None)

# ── Simulation ─────────────────────────────────────────────────────────────────
from server.simulation import Simulation
from server.persistence import init_db, save_simulation, load_simulation, clear_db

init_db()
sim = Simulation()
if load_simulation(sim):
    log.info(f"Loaded saved state at tick {sim.tick_count}")
else:
    log.info("No saved state found, starting fresh")

TICK_RATE = float(os.getenv("TICK_RATE", "1.0"))
SAVE_INTERVAL = 10  # save every N ticks

# Backfill risk_tolerance for ships loaded from old saves
for _s in sim.ships:
    if not hasattr(_s, 'risk_tolerance') or _s.risk_tolerance == 0:
        _s.risk_tolerance = 0.5


def economy_loop():
    while True:
        sim.tick()
        if sim.tick_count % SAVE_INTERVAL == 0:
            save_simulation(sim)
        time.sleep(TICK_RATE)


threading.Thread(target=economy_loop, daemon=True).start()
log.info(f"Economy loop started ({TICK_RATE}s/tick, {len(sim.ships)} NPCs)")


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "game.html")


@app.route("/design")
def design():
    return send_from_directory(BASE_DIR, "design.html")


@app.route("/universe")
def universe_page():
    return send_from_directory(BASE_DIR, "universe.html")


@app.route("/economy")
def economy_page():
    return send_from_directory(BASE_DIR, "economy.html")


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
    return {"status": "ok", "tick": sim.tick_count}


# ── API ────────────────────────────────────────────────────────────────────────
@app.route("/api/state")
def api_state():
    """Full universe state for frontend."""
    systems = {}
    for sid, sys in sim.universe.items():
        stations = []
        for st in sys.stations:
            stations.append({
                "name": st.name,
                "station_type": st.station_type,
                "produces": st.produces,
                "production_rate": st.production_rate,
                "inventory": st.inventory,
                "prices": st.price_cache,
            })
        systems[sid] = {
            "name": sys.name,
            "type": sys.system_type,
            "cluster": sys.cluster,
            "security": sys.security,
            "faction": sys.faction,
            "stations": stations,
            "asteroid_fields": [{"name": a.name, "type": a.field_type, "yields": a.yields, "density": a.density} for a in sys.asteroid_fields],
            "connections": sys.connections,
            "objects": [{"id": o.id, "name": o.name, "type": o.obj_type, "distance": o.distance, "angle": round(o.angle, 4), "connects_to": o.connects_to, "parent": o.parent} for o in sys.objects],
        }
    return jsonify({"tick": sim.tick_count, "systems": systems})


@app.route("/api/ships")
def api_ships():
    """Ship positions and state for the game map."""
    ships = []
    for s in sim.ships:
        ship_data = {
            "name": s.name, "role": s.role, "ship_class": s.ship_class,
            "state": s.state, "location": s.location, "destination": s.destination,
            "progress": round(s.progress, 4), "speed": s.speed, "cargo": s.cargo,
            "intra_position": s.intra_position, "intra_destination": s.intra_destination,
            "intra_progress": round(s.intra_progress, 4), "intra_speed": s.intra_speed,
        }
        # Include origin/dest coordinates for client-side interpolation
        if s.state == "intra_traveling" and s.intra_position and s.intra_destination:
            from_obj = next((o for o in sim.universe[s.location].objects if o.id == s.intra_position), None)
            to_obj = next((o for o in sim.universe[s.location].objects if o.id == s.intra_destination), None)
            if from_obj and to_obj:
                import math
                dist = sim._intra_distance(s.location, s.intra_position, s.intra_destination)
                ship_data["intra_from"] = {"d": from_obj.distance, "a": round(from_obj.angle, 4)}
                ship_data["intra_to"] = {"d": to_obj.distance, "a": round(to_obj.angle, 4)}
                ship_data["intra_dist"] = round(dist, 3)
        ships.append(ship_data)
    return jsonify({"tick": sim.tick_count, "ships": ships})


@app.route("/api/debug")
def api_debug():
    """Debug summary for the monitor page."""
    summary = sim.get_state_summary()
    # Add per-system price snapshot
    prices = {}
    for sid, sys_obj in sim.universe.items():
        for st in sys_obj.stations:
            for commodity, price in st.price_cache.items():
                if st.inventory.get(commodity, 0) > 0:
                    prices.setdefault(commodity, []).append({"system": sys_obj.name, "station": st.name, "price": price, "stock": st.inventory.get(commodity, 0)})
    summary["prices"] = prices
    # Ship details
    ships = []
    for s in sim.ships:
        loc_name = sim.universe[s.location].name if s.location in sim.universe else s.location or "-"
        dest_name = sim.universe[s.destination].name if s.destination in sim.universe else s.destination or "-"
        ships.append({
            "id": s.id, "name": s.name, "state": s.state, "role": s.role,
            "ship_class": s.ship_class, "timer": s.state_timer,
            "location": loc_name, "destination": dest_name,
            "cargo": s.cargo, "progress": round(s.progress, 2),
            "intra_position": s.intra_position, "intra_destination": s.intra_destination,
            "intra_progress": round(s.intra_progress, 3),
        })
    summary["ships"] = ships
    return jsonify(summary)


@app.route("/api/system/<system_id>")
def api_system(system_id):
    """Detailed system view with objects and ship positions."""
    if system_id not in sim.universe:
        return jsonify({"error": "unknown system"}), 404
    sys_obj = sim.universe[system_id]
    objects = [{"id": o.id, "name": o.name, "type": o.obj_type, "distance": o.distance, "angle": round(o.angle, 4), "connects_to": o.connects_to, "parent": o.parent} for o in sys_obj.objects]
    # Ships in this system
    ships_here = []
    for s in sim.ships:
        if s.location == system_id:
            ship_data = {
                "name": s.name, "role": s.role, "state": s.state,
                "intra_position": s.intra_position, "intra_destination": s.intra_destination,
                "intra_progress": round(s.intra_progress, 4), "intra_speed": s.intra_speed,
            }
            if s.state == "intra_traveling" and s.intra_position and s.intra_destination:
                from_obj = next((o for o in sys_obj.objects if o.id == s.intra_position), None)
                to_obj = next((o for o in sys_obj.objects if o.id == s.intra_destination), None)
                if from_obj and to_obj:
                    dist = sim._intra_distance(system_id, s.intra_position, s.intra_destination)
                    ship_data["intra_from"] = {"d": from_obj.distance, "a": round(from_obj.angle, 4)}
                    ship_data["intra_to"] = {"d": to_obj.distance, "a": round(to_obj.angle, 4)}
                    ship_data["intra_dist"] = round(dist, 3)
            ships_here.append(ship_data)
    return jsonify({
        "id": system_id, "name": sys_obj.name, "type": sys_obj.system_type,
        "security": sys_obj.security, "objects": objects, "ships": ships_here,
        "tick": sim.tick_count,
    })


@app.route("/api/nuke", methods=["POST"])
def api_nuke():
    """Reset simulation to initial state."""
    global sim
    clear_db()
    sim = Simulation()
    log.info("NUKE: Simulation reset to initial state")
    return jsonify({"status": "reset", "tick": sim.tick_count})


if __name__ == "__main__":
    import webbrowser
    port = int(os.getenv("PORT", "8000"))
    if not os.getenv("FLY_APP_NAME") and not os.getenv("WERKZEUG_RUN_MAIN"):
        webbrowser.open(f"http://127.0.0.1:{port}")
    app.run(debug=True, host="0.0.0.0", port=port, threaded=True)
