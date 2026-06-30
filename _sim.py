"""Economy sim with progress + results dump. Usage: python _sim.py [ticks]"""
import sys, os, time
sys.path.insert(0, '.')

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 10000

if os.path.exists('data/game.db'):
    os.remove('data/game.db')

import server.main as m
if not m._sim_ready.wait(60):
    print("FAILED to start"); sys.exit(1)

m.supervisor.multiplier = 9999
# Disable only dashboard for speed (faction_events stays active for raids/events)
for w in m.supervisor.workers:
    if w.name == 'dashboard':
        w.tick_interval = 999999
print(f"Running {TARGET} ticks | Results -> sim_results.txt")

start = time.time()
while m.sim.tick_count < TARGET:
    time.sleep(2)
    tick = m.sim.tick_count
    elapsed = time.time() - start
    tps = tick / elapsed if elapsed > 0 else 1
    eta = (TARGET - tick) / tps if tps > 0 else 0
    pct = tick / TARGET * 100
    sys.stdout.write(f"\r  {pct:5.1f}% | tick {tick:>6}/{TARGET} | {tps:.0f} t/s | ETA {int(eta)}s   ")
    sys.stdout.flush()
    if elapsed > 2400: break

tick = m.sim.tick_count
elapsed = time.time() - start
print(f"\n\nDone: {tick} ticks in {elapsed:.0f}s ({tick/elapsed:.0f} t/s) | {tick*6/60/24:.1f} game-days")

universe = m.sim.universe
from server.simulation import COMMODITIES
from collections import Counter

# Price analysis
price_deviations = {}
for sys_id, sys in universe.items():
    for st in sys.stations:
        for com_id, price in st.price_cache.items():
            if com_id in COMMODITIES and COMMODITIES[com_id].base_price > 0:
                ratio = price / COMMODITIES[com_id].base_price
                if com_id not in price_deviations:
                    price_deviations[com_id] = []
                price_deviations[com_id].append(ratio)

all_ratios = [r for rats in price_deviations.values() for r in rats]
within_15 = sum(1 for r in all_ratios if 0.85 <= r <= 1.15)
total = len(all_ratios)

out = []
out.append(f"ECONOMY SIM RESULTS | {tick} ticks | {tick*6/60/24:.1f} days | {tick/elapsed:.0f} t/s")
out.append("=" * 70)
out.append(f"\nPRICE STABILITY ({total:,} points)")
out.append(f"  Within +/-15%: {within_15:,} ({within_15/total*100:.1f}%)")
out.append(f"  Range: {min(all_ratios):.3f}x - {max(all_ratios):.3f}x | Median: {sorted(all_ratios)[total//2]:.3f}x")

buckets = {'<0.5x':0,'0.5-0.85x':0,'0.85-1.15x':0,'1.15-2.0x':0,'>2.0x':0}
for r in all_ratios:
    if r < 0.5: buckets['<0.5x'] += 1
    elif r < 0.85: buckets['0.5-0.85x'] += 1
    elif r <= 1.15: buckets['0.85-1.15x'] += 1
    elif r <= 2.0: buckets['1.15-2.0x'] += 1
    else: buckets['>2.0x'] += 1
out.append("\n  Distribution:")
for k, v in buckets.items():
    out.append(f"    {k:>10}: {v:>6} ({v/total*100:>5.1f}%)")

out.append("\n  Inflated (top 5):")
for cid, rats in sorted(price_deviations.items(), key=lambda x: -sum(x[1])/len(x[1]))[:5]:
    out.append(f"    {COMMODITIES[cid].name:<30} avg:{sum(rats)/len(rats):.2f}x")
out.append("  Crashed (bottom 5):")
for cid, rats in sorted(price_deviations.items(), key=lambda x: sum(x[1])/len(x[1]))[:5]:
    out.append(f"    {COMMODITIES[cid].name:<30} avg:{sum(rats)/len(rats):.2f}x")

# Inventory & growth
total_inv = sum(sum(st.inventory.values()) for sys in universe.values() for st in sys.stations)
out.append(f"\n\nECONOMY HEALTH")
out.append(f"  Inventory: {total_inv:,.0f} | Growth: {total_inv/tick:.0f}/tick")

# Warfare stats
if hasattr(m.sim, 'warfare'):
    w = m.sim.warfare
    out.append(f"  Ships destroyed: {w.ships_destroyed} | Ships built: {w.ships_built}")
    out.append(f"  Destruction rate: {w.ships_destroyed/tick*100:.1f} per 100 ticks")
    out.append(f"  Fleet strength: {sum(sum(f.values()) for f in w.fleets.values())} ships across {len(w.fleets)} factions")

# Fleet
ship_roles = Counter(s.role for s in m.sim.ships)
ship_states = Counter(s.state for s in m.sim.ships)
haulers_active = sum(1 for s in m.sim.ships if s.cargo and s.role in ('hauler','freelance'))
haulers_assigned = sum(1 for s in m.sim.ships if (s.cargo or (hasattr(s, '_contract_dest') and s._contract_dest)) and s.role in ('hauler','freelance'))
cargo_transit = sum(sum(s.cargo.values()) for s in m.sim.ships if s.cargo)
total_haulers = sum(1 for s in m.sim.ships if s.role in ('hauler','freelance'))
out.append(f"\n  Fleet ({len(m.sim.ships)} ships): {dict(ship_roles)}")
out.append(f"  States: {dict(ship_states)}")
out.append(f"  Haulers carrying: {haulers_active} | Assigned (carrying+en_route): {haulers_assigned}/{total_haulers} ({haulers_assigned/max(1,total_haulers)*100:.0f}%) | Cargo: {cargo_transit:,.0f}")

# Shipyard inventory check
out.append("\n  Shipyards:")
for sys_id, sys in universe.items():
    for st in sys.stations:
        if st.station_type == 'shipyard':
            total_st = sum(st.inventory.values())
            out.append(f"    {st.name:<30} inv:{total_st:,.0f} ({sys.faction})")

result = '\n'.join(out)
with open('sim_results.txt', 'w') as f:
    f.write(result)
print(result)
m.supervisor.stop()
