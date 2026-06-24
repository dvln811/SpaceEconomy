"""NPC Decision worker: hauler/miner AI using region inventory cache."""
import math
from server.supervisor import WorkerThread
from server.intents import (
    ShipMoveIntent, ShipIntraIntent, ShipBuyIntent, ShipSellIntent,
    ShipMineIntent, EventLog,
)


BATCH_SIZE = 200  # Process N idle ships per tick (round-robin)


class NPCDecisionWorker(WorkerThread):
    def __init__(self, commodities: dict):
        super().__init__("npc_decisions", tick_interval=1)
        self.commodities = commodities
        self._batch_offset = 0

    def process(self, tick: int, snapshot):
        ships = snapshot['ships']
        universe = snapshot['universe']
        region_cache = snapshot['region_cache']

        # Collect all idle industrial ships
        idle_ships = [s for s in ships if s.state == "idle" and s.role in ("hauler", "miner", "freelance")]
        if not idle_ships:
            return

        # Process up to 200 per tick
        start = self._batch_offset % max(1, len(idle_ships))
        batch = idle_ships[start:start + BATCH_SIZE]
        if len(batch) < BATCH_SIZE:
            batch += idle_ships[:BATCH_SIZE - len(batch)]
        self._batch_offset += BATCH_SIZE

        for ship in batch:
            if ship.role == "miner":
                self._miner_decision(ship, universe, region_cache)
            elif ship.role == "freelance":
                self._freelance_decision(ship, universe, region_cache)
            else:
                self._trader_decision(ship, universe, region_cache)

    def _trader_decision(self, ship, universe, region_cache):
        loc = universe.get(ship.location)
        if not loc:
            return

        # Navigate to a station if not at one
        station_objs = [o for o in loc.objects if o.obj_type == "station"]
        at_station = any(ship.intra_position == o.id for o in station_objs)
        if not at_station and station_objs:
            self.emit(ShipIntraIntent(ship_id=ship.id, dest_obj_id=station_objs[0].id))
            return

        # If carrying cargo, deliver to assigned station
        if ship.cargo:
            if ship.location == ship.assigned_system:
                target = next((st for st in loc.stations if st.name == ship.assigned_station), None)
                if target:
                    # Sell all cargo
                    for commodity, qty in ship.cargo.items():
                        self.emit(ShipSellIntent(
                            ship_id=ship.id, system_id=ship.location,
                            station_name=ship.assigned_station,
                            commodity_id=commodity, quantity=qty
                        ))
                    return
            # Not home, travel there
            self.emit(ShipMoveIntent(ship_id=ship.id, destination=ship.assigned_system))
            return

        # Find what station needs (lowest stock input)
        home_sys = universe.get(ship.assigned_system)
        if not home_sys:
            return
        target = next((st for st in home_sys.stations if st.name == ship.assigned_station), None)
        if not target:
            return

        needed = None
        lowest = float('inf')
        for prod_id in target.produces:
            c = self.commodities.get(prod_id)
            if not c or not c.recipe:
                continue
            for inp_id, qty in c.recipe.items():
                stock = target.inventory.get(inp_id, 0)
                want = qty * target.production_rate * 500
                if stock < want and stock < lowest:
                    lowest = stock
                    needed = inp_id

        if not needed:
            return

        # Use region cache for O(1) lookup instead of iterating systems
        region = home_sys.region
        sources = region_cache.get(region, {}).get(needed, [])

        best_src = None
        best_hops = 999
        for src_sys_id, src_station_name, qty in sources:
            if src_station_name == ship.assigned_station:
                continue
            # Use sec_level directly - ship won't enter if sec_level below threshold
            sys_sec = getattr(universe.get(src_sys_id), 'sec_level', 0.5)
            if sys_sec < (1.0 - ship.risk_tolerance):
                continue
            hops = self._estimate_hops(ship.location, src_sys_id, universe)
            if hops < best_hops:
                best_hops = hops
                best_src = (src_sys_id, src_station_name, qty)

        if not best_src:
            # Fallback: find any high-stock item in region to haul
            import random as _rnd
            region = home_sys.region
            region_items = region_cache.get(region, {})
            if region_items:
                # Pick a random commodity with sources
                candidates = [(sid, stn, cid) for cid, srcs in region_items.items() for sid, stn, qty in srcs if qty > 100 and sid != ship.location]
                if candidates:
                    src_sys_id, src_station_name, commodity_id = _rnd.choice(candidates[:20])
                    self.emit(ShipMoveIntent(ship_id=ship.id, destination=src_sys_id))
                    return
            return

        src_sys_id, src_station_name, available = best_src
        if ship.location == src_sys_id:
            # Buy here
            buy_qty = min(available * 0.5, ship.cargo_capacity)
            if buy_qty > 1:
                route_home = self._find_path(ship.location, ship.assigned_system, ship.risk_tolerance, universe)
                self.emit(ShipBuyIntent(
                    ship_id=ship.id, system_id=src_sys_id,
                    station_name=src_station_name,
                    commodity_id=needed, quantity=buy_qty,
                    route_home=route_home
                ))
        else:
            self.emit(ShipMoveIntent(ship_id=ship.id, destination=src_sys_id))

    def _freelance_decision(self, ship, universe, region_cache):
        """Freelance trader: buy cheap, sell expensive using region cache."""
        import random
        loc = universe.get(ship.location)
        if not loc:
            return

        # Navigate to a station if not at one
        station_objs = [o for o in loc.objects if o.obj_type == "station"]
        at_station = any(ship.intra_position == o.id for o in station_objs)
        if not at_station and station_objs:
            self.emit(ShipIntraIntent(ship_id=ship.id, dest_obj_id=station_objs[0].id))
            return

        # If carrying cargo, sell at local station
        if ship.cargo:
            if loc.stations:
                commodity = next(iter(ship.cargo))
                self.emit(ShipSellIntent(
                    ship_id=ship.id, system_id=ship.location,
                    station_name=loc.stations[0].name,
                    commodity_id=commodity, quantity=ship.cargo[commodity]
                ))
            return

        # Find profitable commodity: high stock somewhere in region
        region = loc.region
        region_items = region_cache.get(region, {})
        best = None
        best_qty = 0
        for commodity_id, sources in region_items.items():
            for src_sys_id, src_station_name, qty in sources:
                if qty > best_qty and src_sys_id != ship.location:
                    sys_sec = getattr(universe.get(src_sys_id, loc), 'sec_level', 0.5)
                    if sys_sec >= (1.0 - ship.risk_tolerance):
                        best = (src_sys_id, src_station_name, commodity_id, qty)
                        best_qty = qty

        if best:
            src_sys_id, src_station_name, commodity_id, qty = best
            if ship.location == src_sys_id:
                buy_qty = min(qty * 0.3, ship.cargo_capacity)
                if buy_qty > 1:
                    self.emit(ShipBuyIntent(
                        ship_id=ship.id, system_id=src_sys_id,
                        station_name=src_station_name,
                        commodity_id=commodity_id, quantity=buy_qty,
                        route_home=[]
                    ))
                    return
            self.emit(ShipMoveIntent(ship_id=ship.id, destination=src_sys_id))
            return

        # Wander
        neighbors = [n for n in loc.connections if getattr(universe.get(n, loc), 'sec_level', 0.5) >= (1.0 - ship.risk_tolerance)]
        if neighbors:
            self.emit(ShipMoveIntent(ship_id=ship.id, destination=random.choice(neighbors)))

    def _miner_decision(self, ship, universe, region_cache):
        loc = universe.get(ship.location)
        if not loc:
            return

        # If cargo heavy, sell at local station or travel to one
        if sum(ship.cargo.values()) >= ship.cargo_capacity * 0.8:
            if loc.stations and ship.cargo:
                # Sell ALL cargo at first available station
                for commodity, qty in list(ship.cargo.items()):
                    self.emit(ShipSellIntent(
                        ship_id=ship.id, system_id=ship.location,
                        station_name=loc.stations[0].name,
                        commodity_id=commodity, quantity=qty
                    ))
                return
            # No station here - travel to assigned system or nearest with one
            if ship.assigned_system and ship.assigned_system != ship.location:
                self.emit(ShipMoveIntent(ship_id=ship.id, destination=ship.assigned_system))
                return
            for neighbor in loc.connections:
                nsys = universe.get(neighbor)
                if nsys and nsys.stations:
                    self.emit(ShipMoveIntent(ship_id=ship.id, destination=neighbor))
                    return
            return

        # Mine if local belts exist
        if loc.asteroid_fields:
            belt_objs = [o for o in loc.objects if o.obj_type == "asteroid_belt"]
            if belt_objs:
                belt_id = belt_objs[0].id
                if ship.intra_position != belt_id:
                    self.emit(ShipIntraIntent(ship_id=ship.id, dest_obj_id=belt_id))
                    return
            self.emit(ShipMineIntent(ship_id=ship.id))
            return

        # No belts here - go to assigned system (home with belts) or find one nearby
        if ship.assigned_system and ship.assigned_system != ship.location:
            self.emit(ShipMoveIntent(ship_id=ship.id, destination=ship.assigned_system))
            return

        # Find nearest system with belts
        for neighbor in loc.connections:
            nsys = universe.get(neighbor)
            if nsys and nsys.asteroid_fields:
                self.emit(ShipMoveIntent(ship_id=ship.id, destination=neighbor))
                return

    def _estimate_hops(self, from_id: str, to_id: str, universe) -> int:
        if from_id == to_id:
            return 0
        a = universe.get(from_id)
        b = universe.get(to_id)
        if not a or not b:
            return 99
        dist = math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)
        return int(dist / 80) + 1

    def _find_path(self, from_id: str, to_id: str, risk_tolerance: float, universe) -> list[str]:
        if from_id == to_id:
            return []
        visited = {from_id}
        queue = [(from_id, [])]
        while queue:
            current, path = queue.pop(0)
            for neighbor in universe[current].connections:
                if neighbor in visited:
                    continue
                sys_sec = getattr(universe.get(neighbor), 'sec_level', 0.5)
                if neighbor != to_id and sys_sec < (1.0 - risk_tolerance):
                    continue
                new_path = path + [neighbor]
                if neighbor == to_id:
                    return new_path
                visited.add(neighbor)
                queue.append((neighbor, new_path))
        return []
