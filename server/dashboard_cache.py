"""Pre-computed dashboard aggregates. Updated every 10 ticks by the dashboard worker."""
import time
from collections import Counter


class DashboardCache:
    def __init__(self):
        self.data = {}

    def update(self, sim, commodities, station_consumption):
        universe = sim.universe
        ships = sim.ships

        # Ships by state
        ships_by_state = Counter(s.state for s in ships)

        # Total inventory (top 20)
        total_inv = Counter()
        for sys in universe.values():
            for st in sys.stations:
                for commodity, qty in st.inventory.items():
                    if qty > 0:
                        total_inv[commodity] += qty
        top_inv = dict(total_inv.most_common(20))

        # Production aggregates
        active = 0
        halted = 0
        bottleneck_counter = Counter()
        for sys in universe.values():
            for st in sys.stations:
                for prod_id in st.produces:
                    com = commodities.get(prod_id)
                    if not com or not com.recipe:
                        continue
                    can_produce = st.production_rate
                    for inp_id, qty_needed in com.recipe.items():
                        avail = st.inventory.get(inp_id, 0)
                        possible = avail / qty_needed if qty_needed > 0 else 999
                        can_produce = min(can_produce, possible)
                    if can_produce <= 0:
                        halted += 1
                        for inp_id, qty_needed in com.recipe.items():
                            if st.inventory.get(inp_id, 0) < qty_needed:
                                bottleneck_counter[commodities[inp_id].name] += 1
                    else:
                        active += 1

        # Ships summary
        by_role = {}
        by_faction_ships = {}
        for s in ships:
            r = s.role or 'unknown'
            if r not in by_role:
                by_role[r] = {'total': 0, 'active': 0}
            by_role[r]['total'] += 1
            if s.state != 'idle':
                by_role[r]['active'] += 1

            f = s.faction or 'independent'
            if f not in by_faction_ships:
                by_faction_ships[f] = {'mil': 0, 'ind': 0}
            if s.role == 'patrol':
                by_faction_ships[f]['mil'] += 1
            else:
                by_faction_ships[f]['ind'] += 1

        # Stations summary
        by_type = {}
        by_faction_stations = {}
        for sys in universe.values():
            faction = sys.faction or 'independent'
            for st in sys.stations:
                t = st.station_type or 'unknown'
                if t not in by_type:
                    by_type[t] = {'total': 0, 'active': 0, 'halted': 0}
                by_type[t]['total'] += 1

                st_halted = 0
                st_active = 0
                for prod_id in st.produces:
                    com = commodities.get(prod_id)
                    if not com or not com.recipe:
                        continue
                    can = st.production_rate
                    for inp_id, qty_needed in com.recipe.items():
                        avail = st.inventory.get(inp_id, 0)
                        can = min(can, avail / qty_needed if qty_needed > 0 else 999)
                    if can <= 0:
                        st_halted += 1
                    else:
                        st_active += 1

                if st_halted > 0 and st_active == 0:
                    by_type[t]['halted'] += 1
                else:
                    by_type[t]['active'] += 1

                if faction not in by_faction_stations:
                    by_faction_stations[faction] = {'total': 0, 'active': 0}
                by_faction_stations[faction]['total'] += 1
                if not (st_halted > 0 and st_active == 0):
                    by_faction_stations[faction]['active'] += 1

        # Demand data (top 20 by demand_per_tick)
        demand_data = {}
        for sys in universe.values():
            for st in sys.stations:
                for prod_id in st.produces:
                    com = commodities.get(prod_id)
                    if not com or not com.recipe:
                        continue
                    for inp_id, qty_needed in com.recipe.items():
                        if inp_id not in demand_data:
                            demand_data[inp_id] = {"demand_per_tick": 0, "total_supply": 0, "name": commodities[inp_id].name}
                        demand_data[inp_id]["demand_per_tick"] += qty_needed * st.production_rate
                for commodity, qty in st.inventory.items():
                    if commodity in demand_data:
                        demand_data[commodity]["total_supply"] += qty
        for v in demand_data.values():
            v["ticks_remaining"] = round(v["total_supply"] / v["demand_per_tick"], 1) if v["demand_per_tick"] > 0 else 9999
            v["deficit"] = round(v["demand_per_tick"] * 100 - v["total_supply"], 1)
        # Keep top 20 by demand
        sorted_demand = sorted(demand_data.items(), key=lambda x: x[1]["demand_per_tick"], reverse=True)
        demand_top = dict(sorted_demand[:40])

        # Prices: top 20 most-stocked commodities with price data
        price_counts = Counter()
        for sys in universe.values():
            for st in sys.stations:
                for commodity in st.price_cache:
                    if st.inventory.get(commodity, 0) > 0.1:
                        price_counts[commodity] += 1
        top_price_ids = [c for c, _ in price_counts.most_common(20)]
        prices = {}
        for sys in universe.values():
            for st in sys.stations:
                for cid in top_price_ids:
                    if cid in st.price_cache and st.inventory.get(cid, 0) > 0.1:
                        prices.setdefault(cid, []).append({
                            "system": sys.name, "station": st.name,
                            "price": round(st.price_cache[cid], 1),
                            "stock": round(st.inventory.get(cid, 0), 1)
                        })
        # Limit each commodity to top 5 entries by stock
        for cid in prices:
            prices[cid] = sorted(prices[cid], key=lambda x: -x["stock"])[:5]

        self.data = {
            'tick': sim.tick_count,
            'uptime_seconds': round(time.time() - sim.start_time),
            'systems': len(universe),
            'npc_ships': len(ships),
            'ships_by_state': dict(ships_by_state),
            'total_inventory': top_inv,
            'trade_volume': sim.trade_volume,
            'recent_events': sim.events[-20:],
            'performance': {},
            'factions': {},
            'production': {
                'active': active,
                'halted': halted,
                'total': active + halted,
                'bottlenecks': [{'name': n, 'count': c} for n, c in bottleneck_counter.most_common(10)],
            },
            'ships_summary': {
                'by_role': by_role,
                'by_faction': by_faction_ships,
            },
            'stations_summary': {
                'by_type': by_type,
                'by_faction': by_faction_stations,
            },
            'demand': demand_top,
            'prices': prices,
            'warfare': {},
        }
