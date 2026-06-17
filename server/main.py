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


@app.route("/debug")
def debug_page():
    return send_from_directory(BASE_DIR, "debug.html")


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
                "inventory": st.inventory,
                "prices": st.price_cache,
                "production": st.production,
                "consumption": st.consumption,
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
        }
    return jsonify({"tick": sim.tick_count, "systems": systems})


@app.route("/api/ships")
def api_ships():
    """Ship positions and state for the game map."""
    ships = []
    for s in sim.ships:
        ships.append({
            "name": s.name, "role": s.role, "ship_class": s.ship_class,
            "state": s.state, "location": s.location, "destination": s.destination,
            "progress": round(s.progress, 2), "cargo": s.cargo,
        })
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
        })
    summary["ships"] = ships
    return jsonify(summary)


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
