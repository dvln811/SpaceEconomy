"""Start local server at 240x speed for browser-based debugging."""
import sys, os
sys.path.insert(0, '.')
os.remove('data/game.db') if os.path.exists('data/game.db') else None

import server.main as m
m._sim_ready.wait(30)
m.supervisor.multiplier = 240
print(f"Server running at http://127.0.0.1:8000 @ 240x speed")
print(f"Ships: {len(m.sim.ships)}, Press Ctrl+C to stop")

# Keep alive (Flask is running in background via gunicorn/threading)
import time
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    m.supervisor.stop()
    print("Stopped.")
