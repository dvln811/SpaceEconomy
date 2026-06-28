"""Detailed economy telemetry - logs per-tick throughput for tracing breakdowns.
Outputs to sim_telemetry.json (may be large - 50-100MB for 10K ticks)."""
import sys, os, time, json
sys.path.insert(0, '.')

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 10000

if os.path.exists('data/game.db'):
    os.remove('data/game.db')

import server.main as m
if not m._sim_ready.wait(60):
    print("FAILED to start"); sys.exit(1)

m.supervisor.multiplier = 9999
print(f"Telemetry run: {TARGET} ticks | Output -> sim_telemetry.json")

# Telemetry data structure
telemetry = {
    'config': {
        'ticks': TARGET,
        'tick_duration_minutes': 6,
    },
    'snapshots': [],  # Every 100 ticks: full state
    'ore_flow': [],   # Every 100 ticks: ore generation vs consumption rates
    'hauler_stats': [],  # Every 100 ticks: what haulers are carrying, where
    'price_history': {},  # commodity_id -> [(tick, avg_price)]
    'mining_output': [],  # Every 100 ticks: total ore produced by miners
    'refinery_throughput': [],  # Every 100 ticks: what refineries consumed/produced
    'military_inventory': [],  # Every 100 ticks: military base stock levels
    'build_projects': [],  # Events: project starts/completions
}

# Track commodities we care about
TRACKED_PRICES = [
    'iron_ore', 'copper_ore', 'palladium_ore', 'neutronium',
    'hydrogen_fuel', 'methane_fuel', 'refined_iron', 'steel_plate',
    'microprocessor', 'armor_compound', 'autocannon', 'missile_launcher',
    'ceramic_plate', 'carbon_composite', 'quartz_crystal',
]
for k in TRACKED_PRICES:
    telemetry['price_history'][k] = []

start = time.time()
last_snapshot = 0

from server.simulation import COMMODITIES

while m.sim.tick_count < TARGET:
    time.sleep(1)
    tick = m.sim.tick_count
    elapsed = time.time() - start
    tps = tick / elapsed if elapsed > 0 else 1
    eta = (TARGET - tick) / tps if tps > 0 else 0
    sys.stdout.write(f"\r  {tick/TARGET*100:5.1f}% | tick {tick:>6}/{TARGET} | {tps:.0f} t/s | ETA {int(eta)}s   ")
    sys.stdout.flush()

    # Snapshot every 100 ticks
    if tick - last_snapshot >= 100:
        last_snapshot = tick
        universe = m.sim.universe

        # --- Ore flow: how much ore exists at mining colonies vs refineries ---
        ore_at_colonies = 0
        ore_at_refineries = 0
        ore_types = ['iron_ore','copper_ore','silicon_ore','titanium_ore','gold_ore',
                     'platinum_ore','palladium_ore','cobalt_ore','nickel_ore','tin_ore',
                     'carbonite','calciumite','neutronium','quartz_crystal','lithium_crystal',
                     'beryllium_crystal','biomass','hydral_ice','methane_ice','nitrogen_ice']
        rare_ores = ['gold_ore','platinum_ore','palladium_ore','neutronium','quartz_crystal',
                     'lithium_crystal','beryllium_crystal']

        colony_ore_detail = {}
        refinery_ore_detail = {}
        rare_at_colonies = 0
        rare_at_refineries = 0

        for sys_id, sysobj in universe.items():
            for st in sysobj.stations:
                if st.station_type == 'mining_colony':
                    for ore in ore_types:
                        qty = st.inventory.get(ore, 0)
                        ore_at_colonies += qty
                        colony_ore_detail[ore] = colony_ore_detail.get(ore, 0) + qty
                        if ore in rare_ores:
                            rare_at_colonies += qty
                elif st.station_type == 'refinery':
                    for ore in ore_types:
                        qty = st.inventory.get(ore, 0)
                        ore_at_refineries += qty
                        refinery_ore_detail[ore] = refinery_ore_detail.get(ore, 0) + qty
                        if ore in rare_ores:
                            rare_at_refineries += qty

        telemetry['ore_flow'].append({
            'tick': tick,
            'ore_at_colonies': round(ore_at_colonies),
            'ore_at_refineries': round(ore_at_refineries),
            'rare_at_colonies': round(rare_at_colonies),
            'rare_at_refineries': round(rare_at_refineries),
            'colony_top5': sorted(colony_ore_detail.items(), key=lambda x:-x[1])[:5],
            'refinery_top5': sorted(refinery_ore_detail.items(), key=lambda x:-x[1])[:5],
            'refinery_empty_ores': [ore for ore in ore_types if refinery_ore_detail.get(ore,0) < 10],
        })

        # --- Hauler stats ---
        haulers_idle = 0
        haulers_carrying = 0
        haulers_traveling = 0
        cargo_by_type = {}
        hauler_destinations = {}
        for s in m.sim.ships:
            if s.role not in ('hauler', 'freelance'):
                continue
            if s.state == 'idle':
                haulers_idle += 1
            elif s.cargo:
                haulers_carrying += 1
                for com, qty in s.cargo.items():
                    cargo_by_type[com] = cargo_by_type.get(com, 0) + qty
            else:
                haulers_traveling += 1

        telemetry['hauler_stats'].append({
            'tick': tick,
            'idle': haulers_idle,
            'carrying': haulers_carrying,
            'traveling': haulers_traveling,
            'top_cargo': sorted(cargo_by_type.items(), key=lambda x:-x[1])[:10],
            'total_cargo': sum(cargo_by_type.values()),
        })

        # --- Miner stats ---
        miners_mining = sum(1 for s in m.sim.ships if s.role == 'miner' and s.state == 'mining')
        miners_traveling = sum(1 for s in m.sim.ships if s.role == 'miner' and s.state in ('traveling','intra_traveling'))
        miners_unloading = sum(1 for s in m.sim.ships if s.role == 'miner' and s.state == 'unloading')
        miners_idle = sum(1 for s in m.sim.ships if s.role == 'miner' and s.state == 'idle')
        miner_cargo = sum(sum(s.cargo.values()) for s in m.sim.ships if s.role == 'miner' and s.cargo)

        telemetry['mining_output'].append({
            'tick': tick,
            'mining': miners_mining,
            'traveling': miners_traveling,
            'unloading': miners_unloading,
            'idle': miners_idle,
            'cargo_held': round(miner_cargo),
        })

        # --- Refinery throughput: check what refined materials exist ---
        refined_totals = {}
        for sys_id, sysobj in universe.items():
            for st in sysobj.stations:
                if st.station_type == 'refinery':
                    for k, v in st.inventory.items():
                        if k not in ore_types:  # outputs (not ore inputs)
                            refined_totals[k] = refined_totals.get(k, 0) + v

        telemetry['refinery_throughput'].append({
            'tick': tick,
            'total_refined_output': round(sum(refined_totals.values())),
            'top_outputs': sorted(refined_totals.items(), key=lambda x:-x[1])[:10],
        })

        # --- Military base inventory ---
        mil_data = []
        for sys_id, sysobj in universe.items():
            for st in sysobj.stations:
                if st.station_type == 'military_base':
                    ammo = sum(v for k, v in st.inventory.items() if 'ammo' in k)
                    weapons = sum(v for k, v in st.inventory.items() if any(w in k for w in ('autocannon','railgun','pulse_laser','missile','beam_laser','flak')))
                    fuel = st.inventory.get('hydrogen_fuel', 0) + st.inventory.get('methane_fuel', 0)
                    mil_data.append({'name': st.name, 'ammo': round(ammo), 'weapons': round(weapons), 'fuel': round(fuel)})
        telemetry['military_inventory'].append({'tick': tick, 'bases': mil_data})

        # --- Price history ---
        price_samples = {}
        sample_count = 0
        for sys_id, sysobj in universe.items():
            for st in sysobj.stations:
                for k in TRACKED_PRICES:
                    if k in st.price_cache:
                        if k not in price_samples:
                            price_samples[k] = []
                        price_samples[k].append(st.price_cache[k])
                sample_count += 1
                if sample_count > 50:
                    break
            if sample_count > 50:
                break

        for k in TRACKED_PRICES:
            if k in price_samples and price_samples[k]:
                avg = sum(price_samples[k]) / len(price_samples[k])
                bp = COMMODITIES[k].base_price if k in COMMODITIES else 1
                telemetry['price_history'][k].append({'tick': tick, 'avg': round(avg, 2), 'ratio': round(avg/bp, 3) if bp > 0 else 0})

        # --- Overall snapshot ---
        total_inv = sum(sum(st.inventory.values()) for sobj in universe.values() for st in sobj.stations)
        telemetry['snapshots'].append({
            'tick': tick,
            'total_inventory': round(total_inv),
            'ships_destroyed': m.sim.warfare.ships_destroyed if hasattr(m.sim, 'warfare') else 0,
            'ships_built': m.sim.warfare.ships_built if hasattr(m.sim, 'warfare') else 0,
            'fleet_strength': sum(sum(f.values()) for f in m.sim.warfare.fleets.values()) if hasattr(m.sim, 'warfare') else 0,
        })

    if elapsed > 2400:
        break

tick = m.sim.tick_count
elapsed = time.time() - start
print(f"\n\nDone: {tick} ticks in {elapsed:.0f}s")

# Write telemetry
with open('sim_telemetry.json', 'w') as f:
    json.dump(telemetry, f, indent=1)
print(f"Telemetry written: {os.path.getsize('sim_telemetry.json') / 1024 / 1024:.1f} MB")

# Quick summary
print("\n--- QUICK SUMMARY ---")
if telemetry['ore_flow']:
    first = telemetry['ore_flow'][0]
    last = telemetry['ore_flow'][-1]
    print(f"  Ore at colonies: {first['ore_at_colonies']:,} -> {last['ore_at_colonies']:,}")
    print(f"  Ore at refineries: {first['ore_at_refineries']:,} -> {last['ore_at_refineries']:,}")
    print(f"  Rare at colonies: {first['rare_at_colonies']:,} -> {last['rare_at_colonies']:,}")
    print(f"  Rare at refineries: {first['rare_at_refineries']:,} -> {last['rare_at_refineries']:,}")
    if last['refinery_empty_ores']:
        print(f"  Refineries STARVED of: {last['refinery_empty_ores']}")
if telemetry['hauler_stats']:
    last_h = telemetry['hauler_stats'][-1]
    print(f"  Haulers: idle={last_h['idle']} carrying={last_h['carrying']} travel={last_h['traveling']}")
    print(f"  Top cargo: {last_h['top_cargo'][:5]}")
if telemetry['mining_output']:
    last_m = telemetry['mining_output'][-1]
    print(f"  Miners: mining={last_m['mining']} idle={last_m['idle']} travel={last_m['traveling']}")
if telemetry['price_history'].get('iron_ore'):
    ph = telemetry['price_history']['iron_ore']
    print(f"  Iron ore price: {ph[0]['ratio']:.2f}x -> {ph[-1]['ratio']:.2f}x")
if telemetry['price_history'].get('palladium_ore'):
    ph = telemetry['price_history']['palladium_ore']
    print(f"  Palladium price: {ph[0]['ratio']:.2f}x -> {ph[-1]['ratio']:.2f}x")

m.supervisor.stop()
