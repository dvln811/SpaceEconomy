"""Economy simulation engine. Runs each tick to update the universe."""
import math
import random
import time
from server.models import (
    System, NPCShip, COMMODITIES, STATION_CONSUMPTION,
    SECURITY_LEVEL, calculate_price
)
from server.universe import build_universe

NPC_TRADER_NAMES = [
    "Meridian Express", "Iron Vagrant", "Solar Wind", "Deep Haul", "Star Drifter",
    "Cobalt Runner", "Void Trader", "Nebula Fox", "Red Kestrel", "Arc Pilgrim",
    "Hull Breaker", "Quiet Flame", "Dust Devil", "Long Reach", "Silver Mule",
    "Copper Saint", "Dusk Hauler", "Pale Orbit", "Cargo Witch", "Tin Prophet",
    "Black Freighter", "Rust Monarch", "Low Tide", "Scrap Baron", "Gray Passage",
    "Fuel Miser", "Ore Hound", "Cold Transit", "Grim Haul", "Last Dividend",
    "Bright Lance", "Warp Minnow", "Slag Heap", "Null Profit", "Chain Link",
    "Dry Run", "Bulk Standard", "Haul Mary", "Penny Wise", "Margin Call",
    "Gilt Edge", "Trade Wind", "Cash Flow", "Ballast King", "Ledger Line",
    "Cargo Cult", "Yield Curve", "Dead Weight", "Stock Pile", "Flat Rate",
    "Iron Price", "Salvage Right", "Fair Trade", "Net Gain", "Cost Plus",
    "Break Even", "Sunk Cost", "Free Port", "Raw Deal", "Short Haul",
]

NPC_MINER_NAMES = [
    "Rock Splitter", "Core Driller", "Vein Seeker", "Dust Eater", "Crater Hog",
    "Belt Crawler", "Pick Axe", "Gravel King", "Deep Bore", "Nugget",
    "Ore Biter", "Drill Bit", "Stone Cold", "Chip Shot", "Core Sample",
    "Strip Mine", "Pay Dirt", "Lode Star", "Slag Rat", "Claim Jumper",
]

LOADING_TICKS = 3
UNLOADING_TICKS = 2
MINING_TICKS = 5


class Simulation:
    def __init__(self):
        self.universe = build_universe()
        self.ships: list[NPCShip] = []
        self.tick_count = 0
        self.start_time = time.time()
        self.events: list[dict] = []
        self.trade_volume = 0
        self._spawn_traders(50)
        self._spawn_miners(20)
        self._bootstrap_seed()
        self._update_all_prices()

    def _bootstrap_seed(self):
        """Seed all producing stations with ~100 ticks of input supply."""
        for sys in self.universe.values():
            for station in sys.stations:
                for prod_id in station.produces:
                    commodity = COMMODITIES.get(prod_id)
                    if not commodity or not commodity.recipe:
                        continue
                    for input_id, qty_needed in commodity.recipe.items():
                        need = qty_needed * station.production_rate * 100
                        current = station.inventory.get(input_id, 0)
                        if current < need:
                            station.inventory[input_id] = need

    def _spawn_traders(self, count: int):
        from server.ship_types import HAULER_SHIPS
        system_ids = list(self.universe.keys())
        hauler_types = list(HAULER_SHIPS.values())
        hauler_factions = ["Trade Guild", "Free Traders", "Industrial Corp", "Agrarian League", "Frontier Logistics"]
        risk_by_tier = {1: 0.2, 2: 0.5, 3: 0.7, 4: 0.9}
        for i in range(count):
            st = hauler_types[i % len(hauler_types)]
            faction = hauler_factions[i % len(hauler_factions)]
            registry = f"HLR-{random.randint(1000,9999)}"
            loc = random.choice(system_ids)
            ship = NPCShip(
                id=f"hauler_{i}", name=f"{st.name} {registry}",
                cargo_capacity=st.cargo_capacity + random.randint(-20, 20),
                fuel=float(st.fuel_capacity), location=loc,
                speed=st.speed, state="idle",
                role="hauler", ship_class=st.id, intra_speed=st.intra_speed,
                risk_tolerance=risk_by_tier.get(st.tier, 0.5), faction=faction,
            )
            station_objs = [o for o in self.universe[loc].objects if o.obj_type == "station"]
            if station_objs:
                ship.intra_position = station_objs[0].id
            self.ships.append(ship)

    def _spawn_miners(self, count: int):
        mining_systems = [sid for sid, sys in self.universe.items() if sys.asteroid_fields]
        from server.ship_types import MINER_SHIPS
        miner_types = list(MINER_SHIPS.values())
        miner_factions = ["Miners Union", "Deep Rock Corp", "Frontier Logistics"]
        risk_by_tier = {1: 0.2, 2: 0.5, 3: 0.8}
        for i in range(count):
            st = miner_types[i % len(miner_types)]
            faction = miner_factions[i % len(miner_factions)]
            registry = f"MNR-{random.randint(1000,9999)}"
            loc = random.choice(mining_systems)
            ship = NPCShip(
                id=f"miner_{i}", name=f"{st.name} {registry}",
                cargo_capacity=st.cargo_capacity + random.randint(-10, 10),
                fuel=float(st.fuel_capacity), location=loc,
                speed=st.speed, state="idle",
                role="miner", ship_class=st.id, intra_speed=st.intra_speed,
                risk_tolerance=risk_by_tier.get(st.tier, 0.5), faction=faction,
            )
            station_objs = [o for o in self.universe[loc].objects if o.obj_type == "station"]
            if station_objs:
                ship.intra_position = station_objs[0].id
            self.ships.append(ship)

    # ── Intra-system helpers ─────────────────────────────────────────────────

    def _get_object(self, system_id: str, obj_id: str):
        for o in self.universe[system_id].objects:
            if o.id == obj_id:
                return o
        return None

    def _get_gate_for(self, system_id: str, dest_system_id: str) -> str:
        for o in self.universe[system_id].objects:
            if o.obj_type == "gate" and o.connects_to == dest_system_id:
                return o.id
        return ""

    def _get_station_obj(self, system_id: str, station_index: int) -> str:
        station_objs = [o for o in self.universe[system_id].objects if o.obj_type == "station"]
        if station_index < len(station_objs):
            return station_objs[station_index].id
        return station_objs[0].id if station_objs else ""

    def _get_belt_obj(self, system_id: str, belt_index: int = 0) -> str:
        belt_objs = [o for o in self.universe[system_id].objects if o.obj_type == "asteroid_belt"]
        if belt_index < len(belt_objs):
            return belt_objs[belt_index].id
        return belt_objs[0].id if belt_objs else ""

    def _intra_distance(self, system_id: str, obj_a_id: str, obj_b_id: str) -> float:
        a = self._get_object(system_id, obj_a_id)
        b = self._get_object(system_id, obj_b_id)
        if not a or not b:
            return 1.0
        ax = a.distance * math.cos(a.angle)
        ay = a.distance * math.sin(a.angle)
        bx = b.distance * math.cos(b.angle)
        by = b.distance * math.sin(b.angle)
        return max(0.5, math.sqrt((ax - bx) ** 2 + (ay - by) ** 2))

    def _start_intra_travel(self, ship: NPCShip, dest_obj_id: str):
        if ship.intra_position == dest_obj_id:
            return
        ship.intra_destination = dest_obj_id
        ship.intra_progress = 0.0
        ship.state = "intra_traveling"

    # ── Safety-aware pathfinding ─────────────────────────────────────────────

    def _system_danger(self, system_id: str) -> float:
        """Return danger value 0-1 for a system (0=safe, 1=deadly)."""
        return 1.0 - SECURITY_LEVEL.get(self.universe[system_id].security, 0.0)

    def _find_path(self, from_id: str, to_id: str, risk_tolerance: float = 1.0) -> list[str]:
        """BFS shortest path, filtering out systems too dangerous for this ship."""
        if from_id == to_id:
            return []
        visited = {from_id}
        queue = [(from_id, [])]
        while queue:
            current, path = queue.pop(0)
            for neighbor in self.universe[current].connections:
                if neighbor in visited:
                    continue
                # Skip systems that are too dangerous (unless it's the destination)
                if neighbor != to_id and self._system_danger(neighbor) > risk_tolerance:
                    continue
                new_path = path + [neighbor]
                if neighbor == to_id:
                    return new_path
                visited.add(neighbor)
                queue.append((neighbor, new_path))
        return []  # no safe path found

    def _send_ship(self, ship: NPCShip, dest_id: str) -> bool:
        path = self._find_path(ship.location, dest_id, ship.risk_tolerance)
        if not path:
            return False
        ship.route_path = path
        ship.destination = path[0]
        gate_id = self._get_gate_for(ship.location, path[0])
        if gate_id and ship.intra_position != gate_id:
            self._start_intra_travel(ship, gate_id)
        else:
            ship.state = "traveling"
            ship.progress = 0.0
        return True

    # ── Tick ─────────────────────────────────────────────────────────────────

    def tick(self):
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
        """Recipe-driven production: consume inputs, produce outputs. Halt on shortage."""
        COMMON_ORES = ["iron_ore", "copper_ore", "ice", "organics"]
        MID_ORES = ["titanium_ore", "helium3"]
        # Rare ores (platinum, crystals, rare_earths, uranium) must be hauled from frontier

        for sys_id, sys in self.universe.items():
            for station in sys.stations:
                # ── Passive ore generation based on security tier ──
                if station.station_type == "mining_colony" and sys.asteroid_fields:
                    for field in sys.asteroid_fields:
                        for ore in field.yields:
                            current = station.inventory.get(ore, 0)
                            if current < 500:
                                station.inventory[ore] = current + 1.5 * field.density

                # Refineries in high-sec passively get common ores (local mining)
                if station.station_type == "refinery" and sys.security in ("high", "medium"):
                    for ore in COMMON_ORES:
                        if any(ore in (COMMODITIES[p].recipe or {}) for p in station.produces):
                            current = station.inventory.get(ore, 0)
                            if current < 200:
                                station.inventory[ore] = current + 0.8

                # Refineries in med-sec also get mid-grade ores
                if station.station_type == "refinery" and sys.security == "medium":
                    for ore in MID_ORES:
                        if any(ore in (COMMODITIES[p].recipe or {}) for p in station.produces):
                            current = station.inventory.get(ore, 0)
                            if current < 200:
                                station.inventory[ore] = current + 0.5

                # ── Passive trade goods generation at hubs/outposts ──
                if station.station_type in ("trade_hub", "frontier_outpost"):
                    from server.models import STATION_CONSUMPTION
                    for tg in STATION_CONSUMPTION.get(station.station_type, []):
                        current = station.inventory.get(tg, 0)
                        if current < 100:
                            station.inventory[tg] = current + 0.5

                # ── Recipe-based production ──
                for commodity_id in station.produces:
                    commodity = COMMODITIES.get(commodity_id)
                    if not commodity or not commodity.recipe:
                        continue
                    can_produce = station.production_rate
                    for input_id, qty_needed in commodity.recipe.items():
                        available = station.inventory.get(input_id, 0)
                        possible = available / qty_needed
                        can_produce = min(can_produce, possible)
                    if can_produce <= 0:
                        continue
                    for input_id, qty_needed in commodity.recipe.items():
                        station.inventory[input_id] = station.inventory.get(input_id, 0) - qty_needed * can_produce
                    station.inventory[commodity_id] = station.inventory.get(commodity_id, 0) + can_produce

                # ── End-use consumption ──
                consumables = STATION_CONSUMPTION.get(station.station_type, [])
                for commodity_id in consumables:
                    station.inventory[commodity_id] = max(0, station.inventory.get(commodity_id, 0) - 0.1)

    def _process_timers(self):
        for ship in self.ships:
            if ship.state in ("loading", "unloading", "mining") and ship.state_timer > 0:
                ship.state_timer -= 1
                if ship.state_timer <= 0:
                    if ship.state == "loading":
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
            ship.cargo[commodity] = ship.cargo.get(commodity, 0) + amount
            self._log(f"{ship.name} mined {amount:.0f}x {COMMODITIES[commodity].name} at {loc.name}")
        if sum(ship.cargo.values()) >= ship.cargo_capacity * 0.8:
            ship.state = "idle"
        else:
            ship.state = "mining"
            ship.state_timer = MINING_TICKS

    def _move_ships(self):
        for ship in self.ships:
            if ship.state != "traveling" or not ship.destination:
                continue
            ship.progress += 0.02 * ship.speed
            if ship.progress >= 1.0:
                ship.progress = 0.0
                ship.location = ship.destination
                arrival_gate = ""
                for o in self.universe[ship.location].objects:
                    if o.obj_type == "gate":
                        arrival_gate = o.id
                        break
                ship.intra_position = arrival_gate if arrival_gate else ""

                if ship.route_path and ship.location == ship.route_path[0]:
                    ship.route_path.pop(0)

                if ship.route_path:
                    next_dest = ship.route_path[0]
                    gate_id = self._get_gate_for(ship.location, next_dest)
                    if gate_id and gate_id != ship.intra_position:
                        ship.destination = next_dest
                        self._start_intra_travel(ship, gate_id)
                    else:
                        ship.destination = next_dest
                        ship.state = "traveling"
                        ship.progress = 0.0
                    self._log(f"{ship.name} transiting {self.universe[ship.location].name}")
                else:
                    ship.destination = ""
                    ship.state = "idle"
                    self._log(f"{ship.name} arrived at {self.universe[ship.location].name}")

    def _move_ships_intra(self):
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
                obj = self._get_object(ship.location, ship.intra_position)
                if obj and obj.obj_type == "gate" and ship.destination and obj.connects_to == ship.destination:
                    ship.state = "traveling"
                    ship.progress = 0.0
                    self._log(f"{ship.name} jumping to {self.universe[ship.destination].name}")
                else:
                    ship.state = "idle"

    # ── NPC Decisions ────────────────────────────────────────────────────────

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

        # Navigate to a station if not at one
        station_objs = [o for o in loc.objects if o.obj_type == "station"]
        at_station = any(ship.intra_position == o.id for o in station_objs)
        if not at_station and station_objs:
            self._start_intra_travel(ship, station_objs[0].id)
            return

        # Unload cargo
        if ship.cargo:
            best_sell = self._find_best_sell(ship, loc)
            if best_sell:
                commodity, station, price = best_sell
                qty = ship.cargo.pop(commodity)
                station.inventory[commodity] = station.inventory.get(commodity, 0) + qty
                self.trade_volume += 1
                ship.state = "unloading"
                ship.state_timer = UNLOADING_TICKS
                self._log(f"{ship.name} unloading {qty:.0f}x {COMMODITIES[commodity].name} at {loc.name}")
                return

        # Find a profitable trade route
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
                ship.route_path = self._find_path(ship.location, dest_id, ship.risk_tolerance)
                ship.destination = ship.route_path[0] if ship.route_path else dest_id
                self._log(f"{ship.name} loading {qty:.0f}x {COMMODITIES[commodity].name}, dest: {self.universe[dest_id].name}")
                return

        # Roam to a reachable neighbor
        safe_neighbors = [n for n in loc.connections if self._system_danger(n) <= ship.risk_tolerance]
        if safe_neighbors:
            self._send_ship(ship, random.choice(safe_neighbors))
        elif loc.connections:
            # Stuck in dangerous space, pick least dangerous exit
            self._send_ship(ship, min(loc.connections, key=lambda n: self._system_danger(n)))

    def _miner_decision(self, ship: NPCShip):
        loc = self.universe[ship.location]

        # If cargo heavy, go sell
        if sum(ship.cargo.values()) >= ship.cargo_capacity * 0.8:
            station_objs = [o for o in loc.objects if o.obj_type == "station"]
            at_station = any(ship.intra_position == o.id for o in station_objs)
            if not at_station and station_objs:
                self._start_intra_travel(ship, station_objs[0].id)
                return
            best_sell = self._find_best_sell(ship, loc)
            if best_sell:
                commodity, station, price = best_sell
                qty = ship.cargo.pop(commodity)
                station.inventory[commodity] = station.inventory.get(commodity, 0) + qty
                ship.state = "unloading"
                ship.state_timer = UNLOADING_TICKS
                self._log(f"{ship.name} selling {qty:.0f}x {COMMODITIES[commodity].name} at {loc.name}")
                return
            # No buyer here, find one within safe range
            for neighbor_id in loc.connections:
                if self._system_danger(neighbor_id) <= ship.risk_tolerance:
                    if self._send_ship(ship, neighbor_id):
                        return
            return

        # Mine if local belts exist
        if loc.asteroid_fields:
            belt_id = self._get_belt_obj(ship.location)
            if belt_id and ship.intra_position != belt_id:
                self._start_intra_travel(ship, belt_id)
                return
            ship.state = "mining"
            ship.state_timer = MINING_TICKS
            return

        # Travel to a system with belts within risk tolerance
        mining_systems = [
            sid for sid, s in self.universe.items()
            if s.asteroid_fields and self._system_danger(sid) <= ship.risk_tolerance
        ]
        if mining_systems:
            target = random.choice(mining_systems)
            self._send_ship(ship, target)

    def _find_best_sell(self, ship: NPCShip, loc: System):
        best = None
        for station in loc.stations:
            for commodity in ship.cargo:
                if commodity not in COMMODITIES:
                    continue
                price = station.price_cache.get(commodity, 0)
                if best is None or price > best[2]:
                    best = (commodity, station, price)
        return best

    def _find_best_trade(self, ship: NPCShip, loc: System):
        """Find best buy-here sell-anywhere-in-cluster opportunity (sector-wide visibility)."""
        best = None
        cluster = loc.cluster
        for station in loc.stations:
            for commodity, stock in station.inventory.items():
                if stock < 5 or commodity not in COMMODITIES:
                    continue
                buy_price = station.price_cache.get(commodity, 999999)
                # Search all systems in same cluster
                for dest_id, dest_sys in self.universe.items():
                    if dest_id == ship.location:
                        continue
                    if dest_sys.cluster != cluster:
                        continue
                    if self._system_danger(dest_id) > ship.risk_tolerance:
                        continue
                    for dest_station in dest_sys.stations:
                        sell_price = dest_station.price_cache.get(commodity, 0)
                        # Discount by hop distance (rough estimate)
                        hops = self._estimate_hops(ship.location, dest_id)
                        discount = max(0.3, 1.0 - hops * 0.1)
                        profit = (sell_price - buy_price) * discount
                        if profit > 0 and (best is None or profit > best[3]):
                            best = (commodity, station, dest_id, profit)
        return best

    def _estimate_hops(self, from_id: str, to_id: str) -> int:
        """BFS hop count estimate."""
        if from_id == to_id:
            return 0
        visited = {from_id}
        queue = [(from_id, 0)]
        while queue:
            current, depth = queue.pop(0)
            if depth > 6:
                return 7
            for neighbor in self.universe[current].connections:
                if neighbor == to_id:
                    return depth + 1
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
        return 7

    def _update_all_prices(self):
        for sys in self.universe.values():
            for station in sys.stations:
                for commodity_id in COMMODITIES:
                    stock = station.inventory.get(commodity_id, 0)
                    demand = 5.0
                    # Stations that produce things want their inputs
                    for prod_id in station.produces:
                        recipe = COMMODITIES[prod_id].recipe
                        if commodity_id in recipe:
                            demand += recipe[commodity_id] * station.production_rate * 10
                    # End-use consumption
                    if commodity_id in STATION_CONSUMPTION.get(station.station_type, []):
                        demand += 20

                    # Dynamic pressure: track unfilled demand / unsold supply over time
                    if not hasattr(station, 'price_pressure'):
                        station.price_pressure = {}
                    pressure = station.price_pressure.get(commodity_id, 0)
                    if demand > 10 and stock < demand:
                        # Unfilled demand: raise buy pressure
                        pressure = min(pressure + 0.5, 50)
                    elif stock > demand * 3:
                        # Oversupply: lower sell pressure
                        pressure = max(pressure - 0.5, -30)
                    else:
                        # Stable: decay toward 0
                        pressure *= 0.98
                    station.price_pressure[commodity_id] = pressure

                    supply = max(1, stock)
                    base_price = calculate_price(commodity_id, supply, demand)
                    # Apply pressure as percentage modifier
                    station.price_cache[commodity_id] = round(base_price * (1 + pressure / 100), 2)

    def _log(self, msg: str):
        self.events.append({"tick": self.tick_count, "time": time.time(), "msg": msg})

    def get_state_summary(self) -> dict:
        ships_by_state = {}
        for s in self.ships:
            ships_by_state[s.state] = ships_by_state.get(s.state, 0) + 1
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
