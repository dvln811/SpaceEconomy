"""Economy stress test with event injection.
Runs baseline, then injects faction build events at intervals to test resilience.
Usage: python sim_events.py [ticks] 
"""
import sys, os, time
sys.path.insert(0, '.')

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 10000

# Event schedule: (tick, description, station_type_target, {commodity_id: quantity_demanded})
# These simulate faction build orders drawing materials from shipyards
EVENTS = [
    (2000, "Terran Fed orders 3 Cruisers", "shipyard", {
        "armor_compound": 6300, "microprocessor": 1900, "propulsion_unit": 1260,
        "reactor_core": 315, "beam_laser_m": 126, "shield_emitter": 90,
    }),
    (4000, "Iron Compact orders Battleship", "shipyard", {
        "armor_compound": 16150, "microprocessor": 3230, "propulsion_unit": 2422,
        "reactor_core": 808, "railgun_m": 162, "armor_laminate": 400,
    }),
    (6000, "Free States emergency ammo resupply", "military_base", {
        "ammo_autocannon_standard_m": 50000, "ammo_missile_launcher_mjolnir_m": 20000,
        "hydrogen_fuel": 10000,
    }),
    (8000, "Merchants Guild station expansion", "shipyard", {
        "armor_compound": 30000, "propulsion_unit": 5000, "reactor_core": 2000,
        "cap_cell": 3000, "warp_coil": 500, "fusion_core": 1000,
    }),
]

if os.path.exists('data/game.db'):
    os.remove('data/game.db')

import server.main as m
if not m._sim_ready.wait(60):
    print("FAILED to start"); sys.exit(1)

m.supervisor.multiplier = 9999
print(f"Event Injection Sim: {TARGET} ticks")
print(f"Events scheduled: {len(EVENTS)}")
for tick, desc, _, _ in EVENTS:
    print(f"  T{tick:>6}: {desc}")
print()

# Track prices of key commodities over time for trend analysis
TRACKED = ['armor_compound', 'microprocessor', 'hydrogen_fuel', 'ammo_autocannon_standard_m', 'iron_ore']
price_history = {k: [] for k in TRACKED}
inventory_history = []

start = time.time()
next_event = 0
last_snapshot = 0

while m.sim.tick_count < TARGET:
    time.sleep(1)
    tick = m.sim.tick_count
    elapsed = time.time() - start
    tps = tick / elapsed if elapsed > 0 else 1
    eta = (TARGET - tick) / tps if tps > 0 else 0
    pct = tick / TARGET * 100

    # Inject events
    while next_event < len(EVENTS) and tick >= EVENTS[next_event][0]:
        ev_tick, desc, st_type, demands = EVENTS[next_event]
        # Find first station of target type and drain its inventory (simulating demand)
        for sys_id, sys in m.sim.universe.items():
            for st in sys.stations:
                if st.station_type == st_type:
                    for com_id, qty in demands.items():
                        # Remove from inventory (simulates materials being consumed for build)
                        current = st.inventory.get(com_id, 0)
                        st.inventory[com_id] = max(0, current - qty)
                    print(f"\n  ** EVENT T{tick}: {desc} (at {st.name}) **")
                    next_event += 1
                    break
            else:
                continue
            break

    # Snapshot every 500 ticks
    if tick - last_snapshot >= 500:
        last_snapshot = tick
        # Sample prices from first trade hub or refinery
        for sys_id, sys in m.sim.universe.items():
            for st in sys.stations:
                if st.station_type in ('trade_hub', 'factory'):
                    for k in TRACKED:
                        price_history[k].append((tick, st.price_cache.get(k, 0)))
                    break
            else:
                continue
            break
        total_inv = sum(sum(st.inventory.values()) for sys in m.sim.universe.values() for st in sys.stations)
        inventory_history.append((tick, total_inv))

    sys.stdout.write(f"\r  [{pct:5.1f}%] tick {tick:>6}/{TARGET} | {tps:.0f} t/s | ETA {int(eta)}s   ")
    sys.stdout.flush()

print(f"\n\nDone: {tick} ticks in {elapsed:.0f}s")

# --- Results ---
out = []
out.append("EVENT INJECTION SIM RESULTS")
out.append(f"Ticks: {tick} | Game days: {tick*6/60/24:.1f}")
out.append("=" * 70)

out.append("\nEVENTS FIRED:")
for t, desc, _, demands in EVENTS:
    total_units = sum(demands.values())
    out.append(f"  T{t:>6}: {desc} ({total_units:,} units demanded)")

out.append("\nINVENTORY TREND (total units across all stations):")
for t, inv in inventory_history:
    out.append(f"  T{t:>6}: {inv:>14,}")
if len(inventory_history) >= 2:
    first = inventory_history[0][1]
    last = inventory_history[-1][1]
    ticks_span = inventory_history[-1][0] - inventory_history[0][0]
    rate = (last - first) / ticks_span if ticks_span > 0 else 0
    out.append(f"\n  Growth rate: {rate:.0f} units/tick ({'ACCUMULATING' if rate > 100 else 'STABLE' if abs(rate) < 100 else 'DEPLETING'})")

out.append("\nPRICE TRENDS (tracked commodities):")
for k in TRACKED:
    if price_history[k]:
        prices = [p for _, p in price_history[k] if p > 0]
        if prices:
            out.append(f"  {k:<35} start:{prices[0]:>8.1f} end:{prices[-1]:>8.1f} min:{min(prices):>8.1f} max:{max(prices):>8.1f}")

# Check recovery: did prices return to normal after events?
out.append("\nRECOVERY ANALYSIS:")
out.append("  (Did prices return to base range after demand shocks?)")
from server.simulation import COMMODITIES
for k in TRACKED:
    if k in COMMODITIES and price_history[k]:
        bp = COMMODITIES[k].base_price
        final_prices = [p for _, p in price_history[k][-3:] if p > 0]
        if final_prices:
            avg_final = sum(final_prices) / len(final_prices)
            ratio = avg_final / bp
            status = "OK" if 0.7 <= ratio <= 1.5 else "STRESSED" if 0.5 <= ratio <= 2.0 else "BROKEN"
            out.append(f"  {k:<35} base:{bp:>8.1f} final:{avg_final:>8.1f} ratio:{ratio:.2f}x [{status}]")

result = '\n'.join(out)
with open('sim_events_results.txt', 'w') as f:
    f.write(result)
print("\n" + result)
print("\n\nSaved to sim_events_results.txt")
m.supervisor.stop()
