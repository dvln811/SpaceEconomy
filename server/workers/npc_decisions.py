"""NPC Decision worker: contract-based hauler AI, miner AI using region inventory cache."""
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
        self._contracts = []  # [{station, sys_id, commodity_id, qty_remaining, region}]
        self._contract_tick = 0

    def process(self, tick: int, snapshot):
        ships = snapshot['ships']
        universe = snapshot['universe']
        region_cache = snapshot['region_cache']

        # Add new contracts every 200 ticks (don't reset existing)
        if tick - self._contract_tick >= 200 or not self._contracts:
            self._refresh_contracts(universe, region_cache)
            self._contract_tick = tick

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
                self._hauler_contract_decision(ship, universe, region_cache)

    def _refresh_contracts(self, universe, region_cache):
        """Add new contracts for station deficits. Don't touch existing in-flight contracts."""
        from server.simulation import STATION_CONSUMPTION
        # Track existing contracts by (sys_id, station, commodity) to avoid duplicates
        existing = set()
        # Prune completed contracts (qty_remaining <= 0)
        self._contracts = [c for c in self._contracts if c['qty_remaining'] > 0]
        for c in self._contracts:
            existing.add((c['sys_id'], c['station'], c['commodity_id']))

        added = 0
        for sys_id, sys in universe.items():
            for st in sys.stations:
                # Recipe input deficits
                for prod_id in st.produces:
                    c = self.commodities.get(prod_id)
                    if not c or not c.recipe:
                        continue
                    for inp_id, qty in c.recipe.items():
                        if (sys_id, st.name, inp_id) in existing:
                            continue
                        stock = st.inventory.get(inp_id, 0)
                        want = qty * st.production_rate * 100
                        if stock < want:
                            self._contracts.append({
                                'sys_id': sys_id, 'station': st.name, 'region': sys.region,
                                'commodity_id': inp_id, 'qty_remaining': want - stock,
                            })
                            existing.add((sys_id, st.name, inp_id))
                            added += 1

                # Consumption deficits
                for commodity_id in STATION_CONSUMPTION.get(st.station_type, []):
                    if (sys_id, st.name, commodity_id) in existing:
                        continue
                    stock = st.inventory.get(commodity_id, 0)
                    if stock < 200:
                        self._contracts.append({
                            'sys_id': sys_id, 'station': st.name, 'region': sys.region,
                            'commodity_id': commodity_id, 'qty_remaining': 500 - stock,
                        })
                        existing.add((sys_id, st.name, commodity_id))
                        added += 1

        # Sort by qty_remaining descending (biggest needs first)
        self._contracts.sort(key=lambda c: -c['qty_remaining'])

    def _hauler_contract_decision(self, ship, universe, region_cache):
        """Pick a contract, claim a portion, go fetch and deliver."""
        import random
        loc = universe.get(ship.location)
        if not loc:
            return

        # Navigate to station if not at one
        station_objs = [o for o in loc.objects if o.obj_type == "station"]
        at_station = any(ship.intra_position == o.id for o in station_objs)
        if not at_station and station_objs:
            self.emit(ShipIntraIntent(ship_id=ship.id, dest_obj_id=station_objs[0].id))
            return

        # If carrying cargo, deliver to contract destination
        if ship.cargo:
            dest = getattr(ship, '_contract_dest', None)
            if dest:
                if ship.location == dest[0]:
                    for commodity, qty in list(ship.cargo.items()):
                        self.emit(ShipSellIntent(
                            ship_id=ship.id, system_id=ship.location,
                            station_name=dest[1],
                            commodity_id=commodity, quantity=qty
                        ))
                    ship._contract_dest = None
                    return
                self.emit(ShipMoveIntent(ship_id=ship.id, destination=dest[0]))
                return
            # No contract dest, sell locally
            if loc.stations:
                for commodity, qty in list(ship.cargo.items()):
                    self.emit(ShipSellIntent(
                        ship_id=ship.id, system_id=ship.location,
                        station_name=loc.stations[0].name,
                        commodity_id=commodity, quantity=qty
                    ))
            return

        # Find a contract - pick from top 20 randomly (weighted by qty), prefer same region
        region = loc.region
        candidates = []
        for c in self._contracts:
            if c['qty_remaining'] <= 0:
                continue
            # Check if source exists
            sources = region_cache.get(c['region'], {}).get(c['commodity_id'], [])
            if not sources:
                # Try other regions
                found = False
                for r, items in region_cache.items():
                    if c['commodity_id'] in items:
                        found = True
                        break
                if not found:
                    continue
            # Prefer same region
            priority = c['qty_remaining']
            if c['region'] == region:
                priority *= 3
            candidates.append((c, priority))
            if len(candidates) >= 30:
                break

        if not candidates:
            return

        # Weighted random from candidates
        weights = [p for _, p in candidates]
        chosen_contract = random.choices([c for c, _ in candidates], weights=weights, k=1)[0]

        # Claim portion (limited by cargo capacity)
        claim = min(ship.cargo_capacity, chosen_contract['qty_remaining'])
        chosen_contract['qty_remaining'] -= claim

        # Find source - prefer closest
        commodity_id = chosen_contract['commodity_id']
        all_sources = []
        for r, items in region_cache.items():
            for src in items.get(commodity_id, []):
                all_sources.append(src)

        if not all_sources:
            chosen_contract['qty_remaining'] += claim  # return claim
            return

        # Sort by distance from ship
        best_src = None
        best_hops = 999
        for src_sys_id, src_station_name, qty in all_sources:
            if qty < 10:
                continue
            hops = self._estimate_hops(ship.location, src_sys_id, universe)
            if hops < best_hops:
                best_hops = hops
                best_src = (src_sys_id, src_station_name, qty)

        if not best_src:
            chosen_contract['qty_remaining'] += claim  # return claim
            return

        # Store destination
        ship._contract_dest = (chosen_contract['sys_id'], chosen_contract['station'])

        src_sys_id, src_station_name, available = best_src
        if ship.location == src_sys_id:
            buy_qty = min(available * 0.5, ship.cargo_capacity, claim)
            if buy_qty > 1:
                self.emit(ShipBuyIntent(
                    ship_id=ship.id, system_id=src_sys_id,
                    station_name=src_station_name,
                    commodity_id=commodity_id, quantity=buy_qty,
                    route_home=[]
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
                # Must be at a station to sell - check intra_position
                station_objs = [o for o in loc.objects if o.obj_type == "station"]
                at_station = any(ship.intra_position == o.id for o in station_objs)
                if not at_station and station_objs:
                    # Travel to station first
                    self.emit(ShipIntraIntent(ship_id=ship.id, dest_obj_id=station_objs[0].id))
                    return
                # At station - sell all cargo
                for commodity, qty in list(ship.cargo.items()):
                    self.emit(ShipSellIntent(
                        ship_id=ship.id, system_id=ship.location,
                        station_name=loc.stations[0].name,
                        commodity_id=commodity, quantity=qty
                    ))
                return
            # No station here - deep miner needs to travel to sell
            # Find target: assigned_station's system (search for it) or nearest with station
            if ship.assigned_station:
                # Find which system has this station
                for nsid in loc.connections:
                    ns = universe.get(nsid)
                    if ns and any(st.name == ship.assigned_station for st in ns.stations):
                        self.emit(ShipMoveIntent(ship_id=ship.id, destination=nsid))
                        return
            # Fallback: any neighbor with a station
            for neighbor in loc.connections:
                nsys = universe.get(neighbor)
                if nsys and nsys.stations:
                    self.emit(ShipMoveIntent(ship_id=ship.id, destination=neighbor))
                    return
            return

        # Mine if local belts exist
        if loc.asteroid_fields:
            belt_objs = [o for o in loc.objects if o.obj_type == "belt"]
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
