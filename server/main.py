import os
import threading
import time
import logging
from flask import Flask, send_from_directory

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("space_economy")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder=None)

# ── Economy tick loop (background thread) ──────────────────────────────────────
TICK_RATE = float(os.getenv("TICK_RATE", "1.0"))
tick_count = 0


def economy_loop():
    global tick_count
    while True:
        tick_count += 1
        # TODO: economy simulation step
        time.sleep(TICK_RATE)


threading.Thread(target=economy_loop, daemon=True).start()


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "mockup.html")


@app.route("/design")
def design():
    return send_from_directory(BASE_DIR, "design.html")


@app.route("/universe")
def universe():
    return send_from_directory(BASE_DIR, "universe.html")


@app.route("/health")
def health():
    return {"status": "ok", "tick": tick_count}


if __name__ == "__main__":
    import webbrowser
    port = int(os.getenv("PORT", "8000"))
    if not os.getenv("FLY_APP_NAME") and not os.getenv("WERKZEUG_RUN_MAIN"):
        webbrowser.open(f"http://127.0.0.1:{port}")
    app.run(debug=True, host="0.0.0.0", port=port, threaded=True)
