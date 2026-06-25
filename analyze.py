"""Deep analysis: 50k ticks, detailed state dumps including market, ships, bottlenecks."""
import sys, time, os, json
from collections import Counter, defaultdict

sys.path.insert(0, '.')
os.remove('data/game.db') if os.path.exists('data/game.db') else None

target_ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
sample_every = int(sys.argv[2]) if len(sys.argv) > 2 else 2500

import server.main as m
from server.simulation import COMMODITIES

m._sim_ready.wait(30)
m.supervisor.multiplier = 480

log_file = 'analysis_deep.json'
samples = []

print(f"Deep analysis: {target_ticks} ticks, sampling every {sample_every}...")
start = time.time()
last_sample = 0

while m.sim.tick_count < target_ticks:
    time.sleep(0.1)
    tick = m.sim.tick_count
    if tick - last_sample >= sample_every:
        last_sample = tick
        elapsed = time.time() - start

        ships = m.sim.ships
        universe = m.sim.universe

        # Ship analysis
        ship_states = Counter(s.state for s in ships)
        role_state = defaultdict(lambda: Counter())
        for s in ships:
            role_state[s.role][s.state] += 1
        
        # Where are ships? (top systems by ship count)
        ship_locations = Counter(s.location for s in ships if s.state != 'idle' or s.role != 'patrol')
        top_ship_systems = ship_locations.most_common(10)

        # Station analysis
        halted_reasons = Counter()
        producing_count = 0
        halted_count = 0
        for sys_obj in universe.values():
            for st in sys_obj.stations:
                if not st.produces:
                    continue
                if st.effective_rate > 0.01:
                    producing_count += 1
                else:
                    halted_count += 1
                    # Find what's missing
                    for prod_id in st.produces:
                        c = COMMODITIES.get(prod_id)
                        if not c or not c.recipe:
                            continue
                        for inp_id, qty in c.recipe.items():
                            if st.inventory.get(inp_id, 0) < qty:
                                halted_reasons[inp_id] += 1
                                break
                        break  # only check first product

        # Inventory analysis
        total_inv = defaultdict(float)
        for sys_obj in universe.values():
            for st in sys_obj.stations:
                for k, v in st.inventory.items():
                    total_inv[k] += v
        
        sorted_inv = sorted(total_inv.items(), key=lambda x: -x[1])
        top_20 = [(k, int(v)) for k, v in sorted_inv[:20]]
        
        # Items with ZERO inventory anywhere
        all_item_ids = set(COMMODITIES.keys())
        items_with_stock = set(k for k, v in total_inv.items() if v > 0)
        zero_stock_items = all_item_ids - items_with_stock
        
        # Overproduced (growing fast)
        overproduced = [(k, int(v)) for k, v in sorted_inv[:5]]
        
        # Trade goods specifically
        trade_good_inv = {k: int(total_inv.get(k, 0)) for k in COMMODITIES if COMMODITIES[k].name and 'Trade Goods' in str(getattr(COMMODITIES[k], 'description', ''))}
        # Actually check by looking at the DB category stored in stats or name
        trade_goods_stock = {}
        for k, v in total_inv.items():
            c = COMMODITIES.get(k)
            if c and hasattr(c, 'tier') and c.tier >= 4 and c.base_price < 15000:
                trade_goods_stock[k] = int(v)

        # Price analysis (sample)
        prices_sample = {}
        for sys_obj in list(universe.values())[:50]:
            for st in sys_obj.stations:
                for k, p in list(st.price_cache.items())[:5]:
                    if k not in prices_sample:
                        prices_sample[k] = []
                    prices_sample[k].append(p)

        # Compute avg prices for a few key items
        key_items = ['iron_ore', 'copper_ore', 'refined_gold', 'platinum_ore', 'hydrogen_fuel', 'steel_plate', 'microprocessor']
        avg_prices = {}
        for k in key_items:
            if k in prices_sample:
                avg_prices[k] = round(sum(prices_sample[k]) / len(prices_sample[k]), 2)

        sample = {
            'tick': tick,
            'elapsed_sec': round(elapsed, 1),
            'ticks_per_sec': round(tick / max(1, elapsed), 1),
            'ship_states': dict(ship_states),
            'role_breakdown': {role: dict(states) for role, states in role_state.items()},
            'top_ship_systems': [(sid, ct) for sid, ct in top_ship_systems],
            'stations_producing': producing_count,
            'stations_halted': halted_count,
            'halted_reasons_top10': halted_reasons.most_common(10),
            'total_inv_qty': int(sum(total_inv.values())),
            'top_20_inventory': top_20,
            'zero_stock_count': len(zero_stock_items),
            'zero_stock_sample': list(zero_stock_items)[:20],
            'trade_goods_stock': trade_goods_stock,
            'avg_prices': avg_prices,
            'trade_volume': m.sim.trade_volume,
            'perf_tick_ms': m.supervisor.metrics.get('tick_ms', 0),
        }
        samples.append(sample)
        
        pct = tick * 100 // target_ticks
        active = sum(v for k, v in ship_states.items() if k != 'idle')
        print(f"  [{pct:3d}%] T{tick:6d} | {sample['ticks_per_sec']:.0f}t/s | active={active} | prod={producing_count}/{producing_count+halted_count} | trades={m.sim.trade_volume} | inv={sample['total_inv_qty']:,} | halted_top={halted_reasons.most_common(3)}")

m.supervisor.stop()

with open(log_file, 'w') as f:
    json.dump(samples, f, indent=2)

# Print summary
print(f"\n{'='*60}")
print(f"ANALYSIS COMPLETE: {len(samples)} samples over {m.sim.tick_count} ticks")
print(f"{'='*60}")
last = samples[-1]
first = samples[0]
print(f"Performance: stable at {last['ticks_per_sec']} t/s")
print(f"Active ships: {sum(v for k,v in last['ship_states'].items() if k!='idle')}/1476")
print(f"Stations: {last['stations_producing']} producing, {last['stations_halted']} halted")
print(f"Inventory growth: {first['total_inv_qty']:,} -> {last['total_inv_qty']:,} ({(last['total_inv_qty']-first['total_inv_qty'])//1000}K growth)")
print(f"Trade volume: {last['trade_volume']:,} total trades")
print(f"\nTop halted reasons:")
for item, count in last['halted_reasons_top10'][:5]:
    name = COMMODITIES[item].name if item in COMMODITIES else item
    print(f"  {name}: {count} stations blocked")
print(f"\nItems with ZERO stock anywhere: {last['zero_stock_count']}")
if last['zero_stock_sample']:
    print(f"  Sample: {[COMMODITIES[k].name if k in COMMODITIES else k for k in last['zero_stock_sample'][:10]]}")
print(f"\nAvg prices: {last['avg_prices']}")
print(f"\nLog written to {log_file}")
