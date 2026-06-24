"""Local dev runner. Starts sim at high speed, prints status every few seconds.
Usage: python dev.py [speed] [duration_seconds]
  speed: tick multiplier (default 120)
  duration: how long to run in seconds (default 60)
"""
import sys, time, os
sys.path.insert(0, '.')

speed = int(sys.argv[1]) if len(sys.argv) > 1 else 120
duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60

# Fresh start
if os.path.exists('data/game.db'):
    os.remove('data/game.db')
    print("Cleared saved state.")

import server.main as m
m._sim_ready.wait(30)
m.supervisor.multiplier = speed
print(f"Running at {speed}x for {duration}s...")

from collections import Counter
start = time.time()
last_print = 0

try:
    while time.time() - start < duration:
        time.sleep(2)
        elapsed = time.time() - start
        tick = m.sim.tick_count
        states = Counter(s.state for s in m.sim.ships)
        roles_active = Counter(s.role for s in m.sim.ships if s.state != 'idle')
        perf = m.supervisor.metrics

        print(f"\n[{elapsed:.0f}s] Tick {tick} ({perf['tick_ms']:.0f}ms/tick, {perf.get('ticks_per_sec',0):.0f} t/s)")
        print(f"  States: idle={states.get('idle',0)} mining={states.get('mining',0)} travel={states.get('traveling',0)+states.get('intra_traveling',0)} load={states.get('loading',0)+states.get('unloading',0)}")
        print(f"  Active by role: {dict(roles_active)}")
        print(f"  Intents/tick: {perf.get('intents_per_tick',0)} | Economy: {perf['worker_times'].get('economy',0):.0f}ms | NPC: {perf['worker_times'].get('npc_decisions',0):.0f}ms")

except KeyboardInterrupt:
    print("\nStopped by user.")

m.supervisor.stop()
print(f"\nFinal: tick {m.sim.tick_count}")
