"""Economy worker: production, consumption, ore generation, price updates."""
from server.supervisor import WorkerThread
from server.intents import InventoryDelta, PriceUpdate, EventLog
from server.models import calculate_price


class EconomyWorker(WorkerThread):
    def __init__(self, commodities: dict, station_consumption: dict):
        super().__init__("economy", tick_interval=1)
        self.commodities = commodities
        self.station_consumption = station_consumption

    def process(self, tick: int, snapshot):
        universe = snapshot['universe']
        self._production_consumption(universe, tick)
        if tick % 10 == 0:
            self._update_prices(universe, tick)

    def _production_consumption(self, universe, tick):
        for sys_id, sys in universe.items():
            for station in sys.stations:
                deltas = {}

                # Passive ore generation
                if sys.asteroid_fields and station.station_type in ('mining_colony', 'refinery', 'trade_hub'):
                    for field in sys.asteroid_fields:
                        for ore in field.yields:
                            current = station.inventory.get(ore, 0)
                            if current < 500000:
                                rate = 50.0 if station.station_type == 'mining_colony' else 20.0
                                deltas[ore] = deltas.get(ore, 0) + rate * field.density

                # Baseline input generation for producing stations
                if station.produces and sys.faction:
                    for prod_id in station.produces:
                        com = self.commodities.get(prod_id)
                        if not com or not com.recipe:
                            continue
                        for inp_id, qty in com.recipe.items():
                            current = station.inventory.get(inp_id, 0) + deltas.get(inp_id, 0)
                            need = qty * station.production_rate * 200
                            if current < need:
                                deltas[inp_id] = deltas.get(inp_id, 0) + qty * station.production_rate * 0.5

                # Passive trade goods generation
                if station.station_type in ("trade_hub", "frontier_outpost"):
                    for tg in self.station_consumption.get(station.station_type, []):
                        current = station.inventory.get(tg, 0) + deltas.get(tg, 0)
                        if current < 100:
                            deltas[tg] = deltas.get(tg, 0) + 0.5

                # Recipe-based production
                for commodity_id in station.produces:
                    commodity = self.commodities.get(commodity_id)
                    if not commodity or not commodity.recipe:
                        continue
                    can_produce = station.production_rate
                    for input_id, qty_needed in commodity.recipe.items():
                        available = station.inventory.get(input_id, 0) + deltas.get(input_id, 0)
                        can_produce = min(can_produce, available / qty_needed)

                    min_ticks_supply = float('inf')
                    for input_id, qty_needed in commodity.recipe.items():
                        available = station.inventory.get(input_id, 0) + deltas.get(input_id, 0)
                        ticks_left = available / max(qty_needed * station.effective_rate, 0.001)
                        min_ticks_supply = min(min_ticks_supply, ticks_left)

                    throttle = min(1.0, min_ticks_supply / 50.0)
                    target_rate = min(can_produce, station.production_rate * throttle)
                    station.effective_rate += (target_rate - station.effective_rate) * 0.02
                    station.effective_rate = max(0, min(station.effective_rate, station.production_rate))
                    actual = min(station.effective_rate, can_produce)
                    if actual < 0.01:
                        continue
                    for input_id, qty_needed in commodity.recipe.items():
                        deltas[input_id] = deltas.get(input_id, 0) - qty_needed * actual
                    deltas[commodity_id] = deltas.get(commodity_id, 0) + actual

                # End-use consumption
                for commodity_id in self.station_consumption.get(station.station_type, []):
                    deltas[commodity_id] = deltas.get(commodity_id, 0) - 0.1

                if deltas:
                    self.emit(InventoryDelta(system_id=sys_id, station_name=station.name, deltas=deltas))

    def _update_prices(self, universe, tick):
        for sys_id, sys in universe.items():
            for station in sys.stations:
                # Only price commodities relevant to this station:
                # items in inventory, items needed as inputs, items consumed
                relevant = set(station.inventory.keys())
                for prod_id in station.produces:
                    recipe = self.commodities.get(prod_id)
                    if recipe and recipe.recipe:
                        relevant.update(recipe.recipe.keys())
                relevant.update(self.station_consumption.get(station.station_type, []))

                if not hasattr(station, 'price_pressure'):
                    station.price_pressure = {}

                for commodity_id in relevant:
                    if commodity_id not in self.commodities:
                        continue
                    stock = station.inventory.get(commodity_id, 0)
                    demand = 5.0
                    for prod_id in station.produces:
                        recipe = self.commodities[prod_id].recipe
                        if commodity_id in recipe:
                            demand += recipe[commodity_id] * station.production_rate * 10
                    if commodity_id in self.station_consumption.get(station.station_type, []):
                        demand += 20

                    pressure = station.price_pressure.get(commodity_id, 0)
                    if demand > 10 and stock < demand:
                        pressure = min(pressure + 0.5, 50)
                    elif stock > demand * 3:
                        pressure = max(pressure - 0.5, -30)
                    else:
                        pressure *= 0.98
                    station.price_pressure[commodity_id] = pressure

                    supply = max(1, stock)
                    base_price = calculate_price(commodity_id, supply, demand, self.commodities)
                    new_price = round(base_price * (1 + pressure / 100), 2)
                    old_price = station.price_cache.get(commodity_id, new_price)

                    if new_price != old_price:
                        self.emit(PriceUpdate(
                            system_id=sys_id, station_name=station.name,
                            commodity_id=commodity_id, new_price=new_price
                        ))
                        if old_price > 0 and stock > 1:
                            pct = (new_price - old_price) / old_price * 100
                            if abs(pct) > 10:
                                name = self.commodities[commodity_id].name
                                direction = "^" if pct > 0 else "v"
                                self.emit(EventLog(tick=tick, msg=f"{direction} {name} {pct:+.0f}% at {station.name} ({sys.name})"))
