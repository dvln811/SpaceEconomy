"""Economy simulation engine. Runs each tick to update the universe."""
import random
import time
from server.models import System, NPCShip, COMMODITIES, calculate_price
from server.universe import build_universe

NPC_TRADER_NAMES = [
    "Meridian Express", "Iron Vagrant", "Solar Wind", "Deep Haul", "Star Drifter",
    "Cobalt Runner", "Void Trader", "Nebula Fox", "Red Kestrel", "Arc Pilgrim",
    "Hull Breaker", "Quiet Flame", "Dust Devil", "Long Reach", "Silver Mule",
    "Copper Saint", "Dusk Hauler", "Pale Orbit", "Cargo Witch", "Tin Prophet",
    "Black Freighter", "Rust Monarch", "Low Tide", "Scrap Baron", "Gray Passage",
    "Fuel Miser", "Ore Hound", "Cold Transit", "Grim Haul", "Last Dividend",
]

NPC_MINER_NAMES = [
    "Rock Splitter", "Core Driller", "Vein Seeker", "Dust Eater", "Crater Hog",
    "Belt Crawler", "Pick Axe", "Gravel King", "Deep Bore", "Nugget",
]

LOADING_TICKS = 3   # ticks to load cargo
UNLOADING_TICKS = 2  # ticks to unload cargo
MINING_TICKS = 5     # ticks per mining cycle


class Simulation:
    def __init__(self):
        self.universe = build_universe()
        self.ships: list[NPCShip] = []
        self.tick_count = 0
        self.start_time = time.time()
        self.events: list[dict] = []
        self.trade_volume = 0
        self._spawn_traders(30)
        self._spawn_miners(10)
        self._update_all_prices()

    def _spawn_traders(self, count: int):
        system_ids = list(self.universe.keys())
        trader_classes = ["Bison Mk.III", "Ox Hauler", "Mule Freighter", "Clydesdale", "Pinto Runner"]
        for i in range(count):
            loc = random.choice(system_ids)
            self.ships.append(NPCShip(
                id=f"trader_{i}", name=NPC_TRADER_NAMES[i % len(NPC_TRADER_NAMES)],
                cargo_capacity=150 + random.randint(0, 200), fuel=100.0,
                location=loc, speed=0.8 + random.random() * 0.6, state="idle", role="trader",
                ship_class=trader_classes[i % len(trader_classes)],
            ))

    def _spawn_miners(self, count: int):
        mining_systems = [sid for sid, sys in self.universe.items() if sys.asteroid_fields]
        miner_classes = ["Burro Driller", "Pickaxe Mk.II", "Anvil Corer"]
        for i in range(count):
            loc = random.choice(mining_systems)
            self.ships.append(NPCShip(
                id=f"miner_{i}", name=NPC_MINER_NAMES[i % len(NPC_MINER_NAMES)],
                cargo_capacity=100 + random.randint(0, 100), fuel=100.0,
                location=loc, speed=0.6 + random.random() * 0.4, state="idle", role="miner",
                ship_class=miner_classes[i % len(miner_classes)],
            ))

    def tick(self):
        """Advance the simulation by one tick."""
        self.tick_count += 1
        self._production_consumption()
        self._process_timers()
        self._move_ships()
        self._npc_decisions()
        self._update_all_prices()
        if len(self.events) > 100:
            self.events = self.events[-100:]

    def _production_consumption(self):
        for sys in self.universe.values():
            for station in sys.stations:
                for commodity, rate in station.production.items():
                    station.inventory.setdefault(commodity, 0)
                    station.inventory[commodity] += rate
                for commodity, rate in station.consumption.items():
                    station.inventory.setdefault(commodity, 0)
                    station.inventory[commodity] = max(0, station.inventory[commodity] - rate)

    def _process_timers(self):
        """Tick down state timers for loading/unloading/mining."""
        for ship in self.ships:
            if ship.state in ("loading", "unloading", "mining") and ship.state_timer > 0:
                ship.state_timer -= 1
                if ship.state_timer <= 0:
                    if ship.state == "loading":
                        # Done loading, now travel to destination
                        ship.state = "traveling"
                        self._log(f"{ship.name} departed {self.universe[ship.location].name} -> {self.universe[ship.destination].name}")
                    elif ship.state == "unloading":
                        ship.state = "idle"
                        self._log(f"{ship.name} finished unloading at {self.universe[ship.location].name}")
                    elif ship.state == "mining":
                        self._complete_mining(ship)

    def _complete_mining(self, ship: NPCShip):
        """Miner finishes a mining cycle, ore goes into cargo."""
        loc = self.universe[ship.location]
        if not loc.asteroid_fields:
            ship.state = "idle"
            return
        field = random.choice(loc.asteroid_fields)
        if not field.yields:
            ship.state = "idle"
            return
        commodity = random.choice(field.yields)
        amount = min(ship.cargo_capacity - sum(ship.cargo.values()), 15 * field.density)
        if amount > 0:
            ship.cargo.setdefault(commodity, 0)
            ship.cargo[commodity] += amount
            self._log(f"{ship.name} mined {amount:.0f}x {COMMODITIES[commodity].name} at {loc.name}")
        # If cargo full, go sell. Otherwise keep mining.
        if sum(ship.cargo.values()) >= ship.cargo_capacity * 0.8:
            ship.state = "idle"  # will trigger sell logic
        else:
            ship.state = "mining"
            ship.state_timer = MINING_TICKS

    def _move_ships(self):
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
        for ship in self.ships:
            if ship.state != "idle":
                continue
            if ship.role == "miner":
                self._miner_decision(ship)
            else:
                self._trader_decision(ship)

    def _trader_decision(self, ship: NPCShip):
        loc = self.universe[ship.location]

        # If carrying cargo, unload and sell
        if ship.cargo:
            best_sell = self._find_best_sell(ship, loc)
            if best_sell:
                commodity, station, price = best_sell
                qty = ship.cargo.pop(commodity)
                station.inventory.setdefault(commodity, 0)
                station.inventory[commodity] += qty
                self.trade_volume += 1
                ship.state = "unloading"
                ship.state_timer = UNLOADING_TICKS
                self._log(f"{ship.name} unloading {qty:.0f}x {COMMODITIES[commodity].name} at {loc.name} ({UNLOADING_TICKS}t)")
                return

        # Try to buy something profitable
        best_route = self._find_best_trade(ship, loc)
        if best_route:
            commodity, buy_station, dest_id, expected_profit = best_route
            available = buy_station.inventory.get(commodity, 0)
            qty = min(available, ship.cargo_capacity)
            if qty > 0:
                buy_station.inventory[commodity] -= qty
                ship.cargo[commodity] = qty
                ship.state = "loading"
                ship.state_timer = LOADING_TICKS
                ship.destination = dest_id
                self._log(f"{ship.name} loading {qty:.0f}x {COMMODITIES[commodity].name} ({LOADING_TICKS}t), dest: {self.universe[dest_id].name}")
                return

        # Nothing good, roam
        if loc.connections:
            ship.destination = random.choice(loc.connections)
            ship.state = "traveling"

    def _miner_decision(self, ship: NPCShip):
        loc = self.universe[ship.location]

        # If cargo is heavy, go sell at nearest station
        if sum(ship.cargo.values()) >= ship.cargo_capacity * 0.8:
            best_sell = self._find_best_sell(ship, loc)
            if best_sell:
                commodity, station, price = best_sell
                qty = ship.cargo.pop(commodity)
                station.inventory.setdefault(commodity, 0)
                station.inventory[commodity] += qty
                ship.state = "unloading"
                ship.state_timer = UNLOADING_TICKS
                self._log(f"{ship.name} selling {qty:.0f}x {COMMODITIES[commodity].name} at {loc.name}")
                return
            # No buyer here, travel to a neighbor
            if loc.connections:
                ship.destination = random.choice(loc.connections)
                ship.state = "traveling"
            return

        # If in a system with asteroids, mine
        if loc.asteroid_fields:
            ship.state = "mining"
            ship.state_timer = MINING_TICKS
            return

        # Travel to a system with asteroids
        mining_neighbors = [c for c in loc.connections if self.universe[c].asteroid_fields]
        if mining_neighbors:
            ship.destination = random.choice(mining_neighbors)
        elif loc.connections:
            ship.destination = random.choice(loc.connections)
        ship.state = "traveling"

    def _find_best_sell(self, ship: NPCShip, loc: System):
        best = None
        for station in loc.stations:
            for commodity in ship.cargo:
                price = station.price_cache.get(commodity, 0)
                if best is None or price > best[2]:
                    best = (commodity, station, price)
        return best

    def _find_best_trade(self, ship: NPCShip, loc: System):
        best = None
        for station in loc.stations:
            for commodity, stock in station.inventory.items():
                if stock < 10:
                    continue
                buy_price = station.price_cache.get(commodity, 999999)
                for neighbor_id in loc.connections:
                    neighbor = self.universe[neighbor_id]
                    for dest_station in neighbor.stations:
                        sell_price = dest_station.price_cache.get(commodity, 0)
                        profit = sell_price - buy_price
                        if profit > 0 and (best is None or profit > best[3]):
                            best = (commodity, station, neighbor_id, profit)
        return best

    def _update_all_prices(self):
        for sys in self.universe.values():
            for station in sys.stations:
                for commodity_id in COMMODITIES:
                    stock = station.inventory.get(commodity_id, 0)
                    demand = station.consumption.get(commodity_id, 1.0) * 10 + 5
                    supply = max(1, stock)
                    station.price_cache[commodity_id] = calculate_price(commodity_id, supply, demand)

    def _log(self, msg: str):
        self.events.append({"tick": self.tick_count, "time": time.time(), "msg": msg})

    def get_state_summary(self) -> dict:
        ships_by_state = {}
        for s in self.ships:
            ships_by_state[s.state] = ships_by_state.get(s.state, 0) + 1
        # Total inventory across all stations
        total_inv = {}
        for sys in self.universe.values():
            for st in sys.stations:
                for commodity, qty in st.inventory.items():
                    if qty > 0:
                        total_inv[commodity] = total_inv.get(commodity, 0) + qty
        return {
            "tick": self.tick_count,
            "uptime_seconds": round(time.time() - self.start_time),
            "systems": len(self.universe),
            "npc_ships": len(self.ships),
            "ships_by_state": ships_by_state,
            "total_inventory": total_inv,
            "trade_volume": self.trade_volume,
            "recent_events": self.events[-20:],
        }
