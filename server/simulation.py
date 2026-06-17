"""Economy simulation engine. Runs each tick to update the universe."""
import random
import time
from server.models import System, NPCShip, COMMODITIES, calculate_price
from server.universe import build_universe

# Ship names for NPC generation
NPC_NAMES = [
    "Meridian Express", "Iron Vagrant", "Solar Wind", "Deep Haul", "Star Drifter",
    "Cobalt Runner", "Void Trader", "Nebula Fox", "Red Kestrel", "Arc Pilgrim",
    "Hull Breaker", "Quiet Flame", "Dust Devil", "Long Reach", "Silver Mule",
    "Copper Saint", "Dusk Hauler", "Pale Orbit", "Cargo Witch", "Tin Prophet",
    "Black Freighter", "Rust Monarch", "Low Tide", "Scrap Baron", "Gray Passage",
    "Fuel Miser", "Ore Hound", "Cold Transit", "Grim Haul", "Last Dividend",
]


class Simulation:
    def __init__(self):
        self.universe = build_universe()
        self.ships: list[NPCShip] = []
        self.tick_count = 0
        self.start_time = time.time()
        self.events: list[dict] = []  # recent events log for debug
        self._spawn_npcs(30)
        self._update_all_prices()

    def _spawn_npcs(self, count: int):
        system_ids = list(self.universe.keys())
        for i in range(count):
            loc = random.choice(system_ids)
            self.ships.append(NPCShip(
                id=f"npc_{i}",
                name=NPC_NAMES[i % len(NPC_NAMES)],
                cargo_capacity=150 + random.randint(0, 200),
                fuel=100.0,
                location=loc,
                speed=0.8 + random.random() * 0.6,
                state="idle",
            ))

    def tick(self):
        """Advance the simulation by one tick."""
        self.tick_count += 1
        self._production_consumption()
        self._move_ships()
        self._npc_decisions()
        self._update_all_prices()
        # Trim event log
        if len(self.events) > 100:
            self.events = self.events[-100:]

    def _production_consumption(self):
        """Each station produces and consumes goods."""
        for sys in self.universe.values():
            for station in sys.stations:
                for commodity, rate in station.production.items():
                    station.inventory.setdefault(commodity, 0)
                    station.inventory[commodity] += rate
                for commodity, rate in station.consumption.items():
                    station.inventory.setdefault(commodity, 0)
                    station.inventory[commodity] = max(0, station.inventory[commodity] - rate)

    def _update_all_prices(self):
        """Recalculate prices at all stations based on current inventory."""
        for sys in self.universe.values():
            for station in sys.stations:
                for commodity_id in COMMODITIES:
                    stock = station.inventory.get(commodity_id, 0)
                    # Demand approximated from consumption rate
                    demand = station.consumption.get(commodity_id, 1.0) * 10 + 5
                    supply = max(1, stock)
                    station.price_cache[commodity_id] = calculate_price(commodity_id, supply, demand)

    def _move_ships(self):
        """Move traveling ships toward their destination."""
        for ship in self.ships:
            if ship.state != "traveling" or not ship.destination:
                continue
            ship.progress += 0.1 * ship.speed
            if ship.progress >= 1.0:
                ship.progress = 0.0
                ship.location = ship.destination
                ship.destination = ""
                ship.state = "idle"
                self._log(f"{ship.name} arrived at {self.universe[ship.location].name}")

    def _npc_decisions(self):
        """Idle NPCs decide what to do: buy, sell, or pick a new destination."""
        for ship in self.ships:
            if ship.state != "idle":
                continue
            loc = self.universe[ship.location]

            # If carrying cargo, try to sell
            if ship.cargo:
                best_sell = self._find_best_sell(ship, loc)
                if best_sell:
                    commodity, station, price = best_sell
                    qty = ship.cargo.pop(commodity)
                    station.inventory.setdefault(commodity, 0)
                    station.inventory[commodity] += qty
                    self._log(f"{ship.name} sold {qty:.0f}x {COMMODITIES[commodity].name} at {loc.name}")
                    continue

            # Try to buy something profitable
            best_route = self._find_best_trade(ship, loc)
            if best_route:
                commodity, buy_station, dest_id, expected_profit = best_route
                # Buy
                available = buy_station.inventory.get(commodity, 0)
                qty = min(available, ship.cargo_capacity)
                if qty > 0:
                    buy_station.inventory[commodity] -= qty
                    ship.cargo[commodity] = qty
                    ship.destination = dest_id
                    ship.state = "traveling"
                    self._log(f"{ship.name} bought {qty:.0f}x {COMMODITIES[commodity].name}, heading to {self.universe[dest_id].name}")
                    continue

            # Nothing good, pick a random neighbor to explore
            if loc.connections:
                ship.destination = random.choice(loc.connections)
                ship.state = "traveling"

    def _find_best_sell(self, ship: NPCShip, loc: System):
        """Find the best commodity to sell at current location."""
        best = None
        for station in loc.stations:
            for commodity in ship.cargo:
                price = station.price_cache.get(commodity, 0)
                if best is None or price > best[2]:
                    best = (commodity, station, price)
        return best

    def _find_best_trade(self, ship: NPCShip, loc: System):
        """Find the most profitable buy-here-sell-there opportunity."""
        best = None
        for station in loc.stations:
            for commodity, stock in station.inventory.items():
                if stock < 10:
                    continue
                buy_price = station.price_cache.get(commodity, 999999)
                # Check neighbors for sell price
                for neighbor_id in loc.connections:
                    neighbor = self.universe[neighbor_id]
                    for dest_station in neighbor.stations:
                        sell_price = dest_station.price_cache.get(commodity, 0)
                        profit = sell_price - buy_price
                        if profit > 0 and (best is None or profit > best[3]):
                            best = (commodity, station, neighbor_id, profit)
        return best

    def _log(self, msg: str):
        self.events.append({"tick": self.tick_count, "time": time.time(), "msg": msg})

    def get_state_summary(self) -> dict:
        """Return a debug-friendly summary of the simulation state."""
        ships_by_state = {"idle": 0, "traveling": 0}
        for s in self.ships:
            ships_by_state[s.state] = ships_by_state.get(s.state, 0) + 1
        return {
            "tick": self.tick_count,
            "uptime_seconds": round(time.time() - self.start_time),
            "systems": len(self.universe),
            "npc_ships": len(self.ships),
            "ships_by_state": ships_by_state,
            "recent_events": self.events[-20:],
        }
