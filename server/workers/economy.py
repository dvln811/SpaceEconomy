"""Economy worker: production, consumption, ore generation, price updates.
Optimized: consumption every tick at 2x, skip idle stations, only emit non-zero deltas."""
from server.supervisor import WorkerThread
from server.intents import InventoryDelta, PriceUpdate, EventLog
from server.models import calculate_price
from server.economy_config import PASSIVE

# Trade good IDs for population consumption
TRADE_GOOD_IDS = [
    "food_rations", "oxygen_packs", "water_recyclers", "life_support_cartridges",
    "housing_materials", "clothing_textiles", "radiation_meds", "emergency_beacons",
    "personal_electronics", "entertainment_systems", "spirits_alcohol", "synthetic_tobacco",
    "cosmetics", "comm_devices", "personal_weapons", "holovid_players", "furniture", "toys_games",
    "ship_repair_kits", "fuel_cells", "escape_pods", "navigation_chips", "stim_packs",
    "neural_implants", "cybernetic_parts", "drone_repair_kits", "industrial_lubricants",
    "exotic_wines", "rare_gems", "quantum_timepieces", "zerog_perfume",
    "synthetic_organs", "memory_crystals", "ai_companions", "art_collections",
]


class EconomyWorker(WorkerThread):
    def __init__(self, commodities: dict, station_consumption: dict):
        super().__init__("economy", tick_interval=1)
        self.commodities = commodities
        self.station_consumption = station_consumption

    def process(self, tick: int, snapshot):
        universe = snapshot['universe']
        do_consumption = True
        self._production(universe, tick, do_consumption)
        if tick % 60 == 0 or tick == 1:
            self._update_prices(universe, tick)
        # Corsair raids: cull excess stockpiles if growth too high
        if tick % 500 == 0 and tick > 0:
            self._corsair_raids(universe, tick)

    def _production(self, universe, tick, do_consumption):
        commodities = self.commodities
        station_consumption = self.station_consumption

        for sys_id, sys in universe.items():
            for station in sys.stations:
                deltas = {}

                # Passive ore generation (only mining colonies with fields)
                if station.station_type == 'mining_colony' and sys.asteroid_fields:
                    for field in sys.asteroid_fields:
                        rate = PASSIVE['rate_multiplier'] * field.density
                        for ore in field.yields:
                            if station.inventory.get(ore, 0) < PASSIVE['inventory_cap']:
                                deltas[ore] = deltas.get(ore, 0) + rate

                # Recipe-based production (skip if station produces nothing)
                if station.produces:
                    # Baseline input trickle: slowly generate recipe inputs so production doesn't completely stall
                    if sys.faction:
                        for prod_id in station.produces:
                            com = commodities.get(prod_id)
                            if not com or not com.recipe:
                                continue
                            for inp_id, qty in com.recipe.items():
                                current = station.inventory.get(inp_id, 0) + deltas.get(inp_id, 0)
                                need = qty * station.production_rate * 200
                                if current < need:
                                    deltas[inp_id] = deltas.get(inp_id, 0) + qty * station.production_rate * 0.3

                    for commodity_id in station.produces:
                        commodity = commodities.get(commodity_id)
                        if not commodity or not commodity.recipe:
                            continue

                        # Check if we can produce (have inputs)
                        can_produce = station.production_rate
                        recipe = commodity.recipe
                        for input_id, qty_needed in recipe.items():
                            available = station.inventory.get(input_id, 0) + deltas.get(input_id, 0)
                            can_produce = min(can_produce, available / qty_needed if qty_needed > 0 else 999)

                        # Throttle based on supply buffer
                        min_ticks = 999.0
                        eff = station.effective_rate
                        if eff > 0.001:
                            for input_id, qty_needed in recipe.items():
                                available = station.inventory.get(input_id, 0) + deltas.get(input_id, 0)
                                t = available / (qty_needed * eff)
                                if t < min_ticks:
                                    min_ticks = t

                        throttle = min(1.0, min_ticks / 50.0)
                        target_rate = min(can_produce, station.production_rate * throttle)
                        station.effective_rate += (target_rate - eff) * 0.02
                        station.effective_rate = max(0.0, min(station.effective_rate, station.production_rate))
                        actual = min(station.effective_rate, can_produce)

                        if actual < 0.01:
                            continue

                        for input_id, qty_needed in recipe.items():
                            deltas[input_id] = deltas.get(input_id, 0) - qty_needed * actual
                        deltas[commodity_id] = deltas.get(commodity_id, 0) + actual

                # End-use consumption (every tick, population-scaled)
                if do_consumption:
                    pop_mult = max(0.5, sys.population / 100_000_000.0)
                    for commodity_id in station_consumption.get(station.station_type, []):
                        rate = 2.0 * pop_mult
                        if station.inventory.get(commodity_id, 0) > rate:
                            deltas[commodity_id] = deltas.get(commodity_id, 0) - rate

                # Shipyard hull-material trickle: slowly generate build_cost materials
                # (only hull inputs, NOT weapons/fittings - those caused price crashes)
                if station.station_type == 'shipyard' and sys.faction:
                    for mat in ('armor_compound', 'propulsion_unit', 'microprocessor',
                                'reactor_core', 'sensor_package', 'warp_coil'):
                        current = station.inventory.get(mat, 0) + deltas.get(mat, 0)
                        if current < 500:
                            deltas[mat] = deltas.get(mat, 0) + 2.0

                # Population-based trade good consumption
                if do_consumption and station.station_type == 'trade_hub' and sys.population > 10000:
                    pop_rate = sys.population / 10_000_000.0  # total units/tick across all goods
                    per_good = pop_rate / len(TRADE_GOOD_IDS)
                    for gid in TRADE_GOOD_IDS:
                        if station.inventory.get(gid, 0) > per_good:
                            deltas[gid] = deltas.get(gid, 0) - per_good

                # Only emit if there are actual non-zero changes
                if deltas:
                    # Filter near-zero values
                    filtered = {k: v for k, v in deltas.items() if abs(v) > 0.001}
                    if filtered:
                        self.emit(InventoryDelta(system_id=sys_id, station_name=station.name, deltas=filtered))

    def _update_prices(self, universe, tick):
        commodities = self.commodities
        station_consumption = self.station_consumption

        for sys_id, sys in universe.items():
            for station in sys.stations:
                # Only price commodities relevant to this station
                relevant = set(station.inventory.keys())
                for prod_id in station.produces:
                    recipe = commodities.get(prod_id)
                    if recipe and recipe.recipe:
                        relevant.update(recipe.recipe.keys())
                relevant.update(station_consumption.get(station.station_type, []))

                if not hasattr(station, 'price_pressure'):
                    station.price_pressure = {}

                for commodity_id in relevant:
                    if commodity_id not in commodities:
                        continue
                    stock = station.inventory.get(commodity_id, 0)
                    demand = 5.0
                    for prod_id in station.produces:
                        recipe = commodities[prod_id].recipe
                        if commodity_id in recipe:
                            demand += recipe[commodity_id] * station.production_rate * 10
                    if commodity_id in station_consumption.get(station.station_type, []):
                        demand += 20

                    pressure = station.price_pressure.get(commodity_id, 0)
                    if demand > 10 and stock < demand:
                        pressure = min(pressure + 0.2, 15)
                    elif stock > demand * 3:
                        pressure = max(pressure - 0.2, -15)
                    else:
                        pressure *= 0.90
                    station.price_pressure[commodity_id] = pressure

                    supply = max(1, stock)
                    base_price = calculate_price(commodity_id, supply, demand, commodities)
                    new_price = round(base_price * (1 + pressure / 100), 2)
                    # Hard clamp: keep prices within reasonable bounds
                    bp = commodities[commodity_id].base_price
                    new_price = max(bp * 0.5, min(bp * 2.0, new_price))
                    old_price = station.price_cache.get(commodity_id)

                    if old_price is None or new_price != old_price:
                        self.emit(PriceUpdate(
                            system_id=sys_id, station_name=station.name,
                            commodity_id=commodity_id, new_price=new_price
                        ))
                        if old_price and old_price > 0 and stock > 1:
                            pct = (new_price - old_price) / old_price * 100
                            if abs(pct) > 10:
                                name = commodities[commodity_id].name
                                direction = "\u25B2" if pct > 0 else "\u25BC"
                                self.emit(EventLog(tick=tick, msg=f"{direction} {name} {pct:+.0f}% at {station.name} ({sys.name})", category='price'))

    def _corsair_raids(self, universe, tick):
        """Dynamic pressure valve: if stockpiles are too high, corsairs raid and cull inventory."""
        import random
        # Calculate total inventory
        total_inv = 0
        stations_with_surplus = []
        for sys_id, sys in universe.items():
            for st in sys.stations:
                st_total = sum(st.inventory.values())
                total_inv += st_total
                if st_total > 50000 and st.station_type in ('mining_colony', 'refinery', 'component_works'):
                    stations_with_surplus.append((sys_id, sys, st, st_total))

        # Only raid if total inventory is growing too fast (> 80M threshold)
        if total_inv < 80_000_000:
            return

        # Raid intensity scales with how far over threshold we are
        excess = total_inv - 80_000_000
        raid_fraction = min(0.15, excess / total_inv)  # max 15% culled per raid cycle

        # Pick random stations to raid
        if not stations_with_surplus:
            return
        num_targets = max(3, len(stations_with_surplus) // 5)
        targets = random.sample(stations_with_surplus, min(num_targets, len(stations_with_surplus)))

        total_lost = 0
        regions_hit = set()
        for sys_id, sys, st, st_total in targets:
            # Cull a fraction of their stockpile
            cull_amount = st_total * raid_fraction
            culled_this = 0
            items = list(st.inventory.items())
            random.shuffle(items)
            for commodity_id, qty in items:
                if culled_this >= cull_amount:
                    break
                take = min(qty * raid_fraction, cull_amount - culled_this)
                if take > 1:
                    st.inventory[commodity_id] = max(0, qty - take)
                    culled_this += take
            total_lost += culled_this
            regions_hit.add(sys.region or 'Unknown')

        # Empire news event
        if total_lost > 0:
            regions_str = ', '.join(list(regions_hit)[:3])
            if len(regions_hit) > 3:
                regions_str += f' +{len(regions_hit)-3} more'
            import random
            templates = [
                f"Coordinated corsair raids sweep through {regions_str}. Merchants report {int(total_lost):,} units of cargo seized.",
                f"Corsair fleets strike supply convoys across {regions_str}. {int(total_lost):,} units lost to piracy.",
                f"Massive pirate offensive hits {regions_str}. Trade networks disrupted, {int(total_lost):,} units of materials stolen.",
            ]
            self.emit(EventLog(tick=tick, msg=f"NEWS: {random.choice(templates)}", category='military'))
            if total_lost > 1_000_000:
                major_templates = [
                    f"EMERGENCY: Corsair armada strikes {len(targets)} stations simultaneously. Faction navies scrambling to respond.",
                    f"Unprecedented pirate offensive - {len(targets)} stations hit in coordinated assault. Security forces overwhelmed.",
                ]
                self.emit(EventLog(tick=tick, msg=f"NEWS: {random.choice(major_templates)}", category='military'))
