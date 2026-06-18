"""Economy simulation engine. Runs each tick to update the universe."""
import math
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
            ship = NPCShip(
                id=f"trader_{i}", name=NPC_TRADER_NAMES[i % len(NPC_TRADER_NAMES)],
                cargo_capacity=150 + random.randint(0, 200), fuel=100.0,
                location=loc, speed=0.8 + random.random() * 0.6, state="idle", role="trader",
                ship_class=trader_classes[i % len(trader_classes)],
            )
            # Place at a station in the system
            station_objs = [o for o in self.universe[loc].objects if o.obj_type == "station"]
            if station_objs:
                ship.intra_position = station_objs[0].id
            self.ships.append(ship)

    def _spawn_miners(self, count: int):
        mining_systems = [sid for sid, sys in self.universe.items() if sys.asteroid_fields]
        miner_classes = ["Burro Driller", "Pickaxe Mk.II", "Anvil Corer"]
        for i in range(count):
            loc = random.choice(mining_systems)
            ship = NPCShip(
                id=f"miner_{i}", name=NPC_MINER_NAMES[i % len(NPC_MINER_NAMES)],
                cargo_capacity=100 + random.randint(0, 100), fuel=100.0,
                location=loc, speed=0.6 + random.random() * 0.4, state="idle", role="miner",
                ship_class=miner_classes[i % len(miner_classes)],
            )
            # Place at a random station in the system
            sys_obj = self.universe[loc]
            station_objs = [o for o in sys_obj.objects if o.obj_type == "station"]
            if station_objs:
                ship.intra_position = station_objs[0].id
            self.ships.append(ship)

    # ── Intra-system helpers ─────────────────────────────────────────────────

    def _get_object(self, system_id: str, obj_id: str):
        """Find a SystemObject by id within a system."""
        for o in self.universe[system_id].objects:
            if o.id == obj_id:
                return o
        return None

    def _get_gate_for(self, system_id: str, dest_system_id: str) -> str:
        """Find the gate object_id in system_id that connects to dest_system_id."""
        for o in self.universe[system_id].objects:
            if o.obj_type == "gate" and o.connects_to == dest_system_id:
                return o.id
        return ""

    def _get_station_obj(self, system_id: str, station_index: int) -> str:
        """Get the object_id for a station by its index."""
        station_objs = [o for o in self.universe[system_id].objects if o.obj_type == "station"]
        if station_index < len(station_objs):
            return station_objs[station_index].id
        return station_objs[0].id if station_objs else ""

    def _get_belt_obj(self, system_id: str, belt_index: int = 0) -> str:
        """Get the object_id for an asteroid belt."""
        belt_objs = [o for o in self.universe[system_id].objects if o.obj_type == "asteroid_belt"]
        if belt_index < len(belt_objs):
            return belt_objs[belt_index].id
        return belt_objs[0].id if belt_objs else ""

    def _intra_distance(self, system_id: str, obj_a_id: str, obj_b_id: str) -> float:
        """Calculate distance between two objects in a system (AU)."""
        a = self._get_object(system_id, obj_a_id)
        b = self._get_object(system_id, obj_b_id)
        if not a or not b:
            return 1.0
        # Convert polar to cartesian and measure
        ax = a.distance * math.cos(a.angle)
        ay = a.distance * math.sin(a.angle)
        bx = b.distance * math.cos(b.angle)
        by = b.distance * math.sin(b.angle)
        return max(0.5, math.sqrt((ax - bx) ** 2 + (ay - by) ** 2))

    def _start_intra_travel(self, ship: NPCShip, dest_obj_id: str):
        """Start a ship moving to a destination object within its current system."""
        if ship.intra_position == dest_obj_id:
            return  # already there
        ship.intra_destination = dest_obj_id
        ship.intra_progress = 0.0
        ship.state = "intra_traveling"

    def tick(self):
        """Advance the simulation by one tick."""
        self.tick_count += 1
        self._production_consumption()
        self._process_timers()
        self._move_ships()
        self._move_ships_intra()
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
                        # Done loading, navigate to gate then jump
                        if ship.destination:
                            gate_id = self._get_gate_for(ship.location, ship.route_path[0] if ship.route_path else ship.destination)
                            if gate_id and ship.intra_position != gate_id:
                                self._start_intra_travel(ship, gate_id)
                                self._log(f"{ship.name} heading to gate in {self.universe[ship.location].name}")
                            else:
                                ship.state = "traveling"
                                self._log(f"{ship.name} departed {self.universe[ship.location].name}")
                        else:
                            ship.state = "idle"
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

    def _find_path(self, from_id: str, to_id: str) -> list[str]:
        """BFS shortest path. Returns list of system IDs (excluding from_id)."""
        if from_id == to_id:
            return []
        visited = {from_id}
        queue = [(from_id, [])]
        while queue:
            current, path = queue.pop(0)
            for neighbor in self.universe[current].connections:
                if neighbor in visited:
                    continue
                new_path = path + [neighbor]
                if neighbor == to_id:
                    return new_path
                visited.add(neighbor)
                queue.append((neighbor, new_path))
        return []  # no path found

    def _send_ship(self, ship: NPCShip, dest_id: str):
        """Set a ship traveling along the shortest path to dest_id."""
        path = self._find_path(ship.location, dest_id)
        if not path:
            return False
        ship.route_path = path
        ship.destination = path[0]
        # First, travel to the gate within the current system
        gate_id = self._get_gate_for(ship.location, path[0])
        if gate_id and ship.intra_position != gate_id:
            self._start_intra_travel(ship, gate_id)
        else:
            # Already at gate (or no gate), jump immediately
            ship.state = "traveling"
            ship.progress = 0.0
        return True

    def _move_ships(self):
        """Handle inter-system travel between gates. Ships progress between systems."""
        for ship in self.ships:
            if ship.state != "traveling" or not ship.destination:
                continue
            ship.progress += 0.02 * ship.speed
            if ship.progress >= 1.0:
                # Arrived at destination system
                ship.progress = 0.0
                ship.location = ship.destination
                # Place at the arrival gate
                arrival_gate = ""
                for o in self.universe[ship.location].objects:
                    if o.obj_type == "gate":
                        arrival_gate = o.id
                        break
                ship.intra_position = arrival_gate if arrival_gate else ""

                # Advance route path
                if ship.route_path and ship.location == ship.route_path[0]:
                    ship.route_path.pop(0)

                if ship.route_path:
                    # More hops: travel to the next gate within this system
                    next_dest = ship.route_path[0]
                    gate_id = self._get_gate_for(ship.location, next_dest)
                    if gate_id and gate_id != ship.intra_position:
                        ship.destination = next_dest
                        self._start_intra_travel(ship, gate_id)
                    else:
                        # Already at the right gate, jump again
                        ship.destination = next_dest
                        ship.state = "traveling"
                        ship.progress = 0.0
                    self._log(f"{ship.name} transiting {self.universe[ship.location].name}")
                else:
                    # Final destination reached, go to station
                    ship.destination = ""
                    ship.state = "idle"
                    self._log(f"{ship.name} arrived at {self.universe[ship.location].name}")

    def _move_ships_intra(self):
        """Handle intra-system movement between objects."""
        for ship in self.ships:
            if ship.state != "intra_traveling" or not ship.intra_destination:
                continue
            dist = self._intra_distance(ship.location, ship.intra_position or f"{ship.location}_star", ship.intra_destination)
            step = ship.intra_speed / max(dist, 0.5)
            ship.intra_progress += step
            if ship.intra_progress >= 1.0:
                ship.intra_position = ship.intra_destination
                ship.intra_destination = ""
                ship.intra_progress = 0.0
                # Check if we arrived at a gate and need to jump
                obj = self._get_object(ship.location, ship.intra_position)
                if obj and obj.obj_type == "gate" and ship.destination and obj.connects_to == ship.destination:
                    # Start inter-system travel
                    ship.state = "traveling"
                    ship.progress = 0.0
                    self._log(f"{ship.name} jumping to {self.universe[ship.destination].name}")
                else:
                    ship.state = "idle"
                    self._log(f"{ship.name} reached {obj.name if obj else 'destination'} in {self.universe[ship.location].name}")

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

        # If not at a station, travel to one first
        station_objs = [o for o in loc.objects if o.obj_type == "station"]
        at_station = any(ship.intra_position == o.id for o in station_objs)

        if not at_station and station_objs:
            # Go to the first station
            self._start_intra_travel(ship, station_objs[0].id)
            return

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
                ship.route_path = self._find_path(ship.location, dest_id)
                ship.destination = ship.route_path[0] if ship.route_path else dest_id
                self._log(f"{ship.name} loading {qty:.0f}x {COMMODITIES[commodity].name} ({LOADING_TICKS}t), dest: {self.universe[dest_id].name}")
                return

        # Nothing good, roam to a random system within 2 hops
        if loc.connections:
            self._send_ship(ship, random.choice(loc.connections))

    def _miner_decision(self, ship: NPCShip):
        loc = self.universe[ship.location]

        # If cargo is heavy, go sell at nearest station
        if sum(ship.cargo.values()) >= ship.cargo_capacity * 0.8:
            # Check if at a station
            station_objs = [o for o in loc.objects if o.obj_type == "station"]
            at_station = any(ship.intra_position == o.id for o in station_objs)

            if not at_station and station_objs:
                self._start_intra_travel(ship, station_objs[0].id)
                return

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
            # No buyer here, find one
            if loc.connections:
                self._send_ship(ship, random.choice(loc.connections))
            return

        # If in a system with asteroids, navigate to belt and mine
        if loc.asteroid_fields:
            belt_id = self._get_belt_obj(ship.location)
            if belt_id and ship.intra_position != belt_id:
                self._start_intra_travel(ship, belt_id)
                return
            ship.state = "mining"
            ship.state_timer = MINING_TICKS
            return

        # Travel to a system with asteroids
        mining_systems = [sid for sid, s in self.universe.items() if s.asteroid_fields]
        if mining_systems:
            target = random.choice(mining_systems)
            self._send_ship(ship, target)
        elif loc.connections:
            self._send_ship(ship, random.choice(loc.connections))

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
        checked = set()
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
                    # 2nd hop
                    for hop2_id in neighbor.connections:
                        if hop2_id == ship.location:
                            continue
                        hop2 = self.universe[hop2_id]
                        for dest_station in hop2.stations:
                            sell_price = dest_station.price_cache.get(commodity, 0)
                            profit = (sell_price - buy_price) * 0.8
                            if profit > 0 and (best is None or profit > best[3]):
                                best = (commodity, station, hop2_id, profit)
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
