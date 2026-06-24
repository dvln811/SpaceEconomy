"""Economy simulation engine. Runs each tick to update the universe."""
import math
import random
import time
from server.models import System, NPCShip, SECURITY_LEVEL, calculate_price, Commodity
from server.data_access import load_commodities, load_station_consumption, load_universe

# All data loaded from game_data.db
COMMODITIES = load_commodities()
STATION_CONSUMPTION = load_station_consumption()

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
        self.universe = load_universe()
        # Factions already assigned in DB data
        self.ships: list[NPCShip] = []
        self.tick_count = 0
        self.start_time = time.time()
        self.events: list[dict] = []
        self.trade_volume = 0
        self._populate_universe()
        self._bootstrap_seed()
        # Warfare simulation
        from server.warfare import WarfareSimulation
        self.warfare = WarfareSimulation()

    def _bootstrap_seed(self):
        """Demand-driven seeding: seed each station with enough inputs for 100 ticks
        of production, plus seed mining colonies with raw ores scaled to demand."""
        BUFFER = 100
        # Seed producing stations with inputs
        for sys in self.universe.values():
            for station in sys.stations:
                for prod_id in station.produces:
                    commodity = COMMODITIES.get(prod_id)
                    if not commodity or not commodity.recipe:
                        continue
                    for input_id, qty_needed in commodity.recipe.items():
                        need = qty_needed * station.production_rate * BUFFER
                        station.inventory[input_id] = max(station.inventory.get(input_id, 0), need)
                # Also seed some output stock
                for prod_id in station.produces:
                    station.inventory[prod_id] = max(station.inventory.get(prod_id, 0), station.production_rate * 100)

        # Seed mining colonies with large ore stocks (based on what the economy needs)
        # Common ores: 10000+, uncommon: 5000, rare: 1000, exotic: 200
        ORE_SEEDS = {
            'iron_ore': 15000, 'copper_ore': 12000, 'calcite': 5000, 'carbonite': 8000,
            'hydral_ice': 20000, 'silicon_ore': 8000,
            'cobalt_ore': 5000, 'zinc_ore': 3000, 'tin_ore': 3000,
            'nitrogen_ice': 12000, 'methane_ice': 5000, 'biomass': 10000, 'nickel_ore': 3000,
            'titanium_ore': 3000, 'tungsten_ore': 2000, 'chromium_ore': 2000,
            'helium3': 1500, 'xenon_gas': 2000, 'spore_clusters': 1500, 'amino_gel': 1500,
            'platinum_ore': 500, 'gold_ore': 500, 'palladium_ore': 300,
            'quartz_crystal': 600, 'lithium_crystal': 800, 'beryllium_crystal': 400,
            'kraxolite': 100, 'void_shard': 50, 'neutronium': 30,
        }
        for sys in self.universe.values():
            for station in sys.stations:
                if station.station_type == 'mining_colony':
                    for ore_id, amount in ORE_SEEDS.items():
                        # Only seed ores that this system's fields can produce
                        field_yields = set()
                        for f in sys.asteroid_fields:
                            field_yields.update(f.yields)
                        if ore_id in field_yields:
                            station.inventory[ore_id] = max(station.inventory.get(ore_id, 0), amount)

        # Seed trade hubs with trade goods
        for sys in self.universe.values():
            for station in sys.stations:
                if station.station_type in ('trade_hub', 'frontier_outpost'):
                    for tg in STATION_CONSUMPTION.get(station.station_type, []):
                        station.inventory[tg] = max(station.inventory.get(tg, 0), 2000)

    def _populate_universe(self):
        """Create a living universe: industrial ships + military fleets."""
        from server.data_access import load_ship_types
        all_ships = load_ship_types()
        hauler_types = [s for s in all_ships.values() if s.role == 'Industrial']
        miner_types = [s for s in all_ships.values() if s.role == 'Mining Barge']

        ship_idx = 0

        # --- Industrial ships: haulers & freelancers ---
        # ~4 per system that has stations (~600 haulers/freelancers)
        for sys_id, sys in self.universe.items():
            if not sys.stations:
                continue
            for i in range(4):
                st = hauler_types[ship_idx % len(hauler_types)]
                role = "freelance" if random.random() < 0.2 else "hauler"
                station = sys.stations[i % len(sys.stations)]
                ship = NPCShip(
                    id=f"hlr_{ship_idx}", name=f"{st.name} {random.randint(100,999)}",
                    cargo_capacity=st.cargo_capacity + random.randint(-20, 20),
                    fuel=float(st.fuel_capacity), location=sys_id,
                    speed=st.speed, state="idle",
                    role=role, ship_class=st.id, intra_speed=st.intra_speed,
                    risk_tolerance=random.uniform(0.3, 0.8), faction=sys.faction or "independent",
                    align_time=st.align_time,
                    assigned_station=station.name if role == "hauler" else "",
                    assigned_system=sys_id if role == "hauler" else "",
                )
                station_objs = [o for o in sys.objects if o.obj_type == "station"]
                if station_objs:
                    ship.intra_position = station_objs[i % len(station_objs)].id
                self.ships.append(ship)
                ship_idx += 1

        # --- Miners: 2 per mining system (~400 miners) ---
        miner_idx = 0
        mining_systems = [sid for sid, s in self.universe.items() if s.asteroid_fields]
        random.shuffle(mining_systems)
        for sys_id in mining_systems[:200]:
            sys = self.universe[sys_id]
            for i in range(2):
                st = miner_types[miner_idx % len(miner_types)]
                ship = NPCShip(
                    id=f"mnr_{miner_idx}", name=f"{st.name} {random.randint(100,999)}",
                    cargo_capacity=st.cargo_capacity + random.randint(-10, 10),
                    fuel=float(st.fuel_capacity), location=sys_id,
                    speed=st.speed, state="idle",
                    role="miner", ship_class=st.id, intra_speed=st.intra_speed,
                    risk_tolerance=random.uniform(0.2, 0.7), faction=sys.faction or "independent",
                    align_time=st.align_time,
                )
                station_objs = [o for o in sys.objects if o.obj_type == "station"]
                if station_objs:
                    ship.intra_position = station_objs[0].id
                self.ships.append(ship)
                miner_idx += 1

        # --- Military ships: faction fleets ---
        from server.game_data_db import get_data_db
        conn = get_data_db()
        conn.row_factory = __import__('sqlite3').Row

        fleet_targets = {
            "terran_fed": 80, "merchants_guild": 120, "free_states": 110,
            "iron_compact": 100, "science_collective": 110, "corsairs": 60,
        }
        # Composition: 40% fighters, 25% frigates, 15% destroyers, 10% cruisers, 7% BCs, 3% BSs
        composition = [
            ("Fighter", 0.40), ("Frigate", 0.25), ("Destroyer", 0.15),
            ("Cruiser", 0.10), ("Battlecruiser", 0.07), ("Battleship", 0.03),
        ]

        mil_idx = 0
        for faction_id, total in fleet_targets.items():
            # Get faction's systems for spreading ships
            faction_systems = [sid for sid, s in self.universe.items() if s.faction == faction_id]
            if not faction_systems:
                continue
            # Get faction's military ships by hull class
            faction_ships = {}
            rows = conn.execute("SELECT id, name, hull_class FROM ships WHERE faction_id=? AND hull_class NOT IN ('Carrier','Dreadnought')", (faction_id,)).fetchall()
            for r in rows:
                faction_ships.setdefault(r["hull_class"], []).append((r["id"], r["name"]))

            for hull_class, pct in composition:
                count = max(1, int(total * pct))
                variants = faction_ships.get(hull_class, [])
                if not variants:
                    continue
                for i in range(count):
                    ship_def = variants[i % len(variants)]
                    sys_id = faction_systems[mil_idx % len(faction_systems)]
                    ship = NPCShip(
                        id=f"mil_{mil_idx}", name=f"{ship_def[1]} {random.randint(100,999)}",
                        cargo_capacity=0, fuel=100.0, location=sys_id,
                        speed=1.0, state="idle",
                        role="patrol", ship_class=ship_def[0], intra_speed=0.2,
                        risk_tolerance=1.0, faction=faction_id,
                        align_time=5,
                    )
                    self.ships.append(ship)
                    mil_idx += 1

        conn.close()

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
        ship.intra_progress = -ship.align_time  # negative = aligning (ticks until 0)
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
        if self.tick_count % 10 == 0:
            self._update_all_prices()
        # Warfare: skirmishes consume ships, shipyards rebuild
        war_events = self.warfare.tick(self.tick_count, self.universe)
        for e in war_events:
            self._log(f"BATTLE: {e['attacker']} vs {e['defender']} ({e['a_losses']}+{e['d_losses']} ships lost)")
        if self.tick_count % 50 == 0:
            build_events = self.warfare.try_build_ships(self.universe)
            for msg in build_events:
                self._log(msg)
        # Faction-level summary events every 200 ticks
        if self.tick_count % 200 == 0:
            self._generate_faction_events()
        if len(self.events) > 100:
            self.events = self.events[-100:]

    def _production_consumption(self):
        """Recipe-driven production: consume inputs, produce outputs. Halt on shortage."""
        for sys_id, sys in self.universe.items():
            for station in sys.stations:
                # ── Passive ore generation for stations in systems with asteroid fields ──
                if sys.asteroid_fields and station.station_type in ('mining_colony', 'refinery', 'trade_hub'):
                    for field in sys.asteroid_fields:
                        for ore in field.yields:
                            current = station.inventory.get(ore, 0)
                            if current < 500000:
                                rate = 50.0 if station.station_type == 'mining_colony' else 20.0
                                station.inventory[ore] = current + rate * field.density
                
                # ── Baseline T1/T2 input generation for producing stations (abstract local economy) ──
                if station.produces and sys.faction:
                    for prod_id in station.produces:
                        com = COMMODITIES.get(prod_id)
                        if not com or not com.recipe:
                            continue
                        for inp_id, qty in com.recipe.items():
                            current = station.inventory.get(inp_id, 0)
                            need = qty * station.production_rate * 200
                            if current < need:
                                station.inventory[inp_id] = current + qty * station.production_rate * 0.5

                # ── Passive trade goods generation at hubs/outposts ──
                if station.station_type in ("trade_hub", "frontier_outpost"):
                    for tg in STATION_CONSUMPTION.get(station.station_type, []):
                        current = station.inventory.get(tg, 0)
                        if current < 100:
                            station.inventory[tg] = current + 0.5

                # ── Recipe-based production (self-limiting) ──
                for commodity_id in station.produces:
                    commodity = COMMODITIES.get(commodity_id)
                    if not commodity or not commodity.recipe:
                        continue
                    # Calculate max possible from available inputs
                    can_produce = station.production_rate
                    for input_id, qty_needed in commodity.recipe.items():
                        available = station.inventory.get(input_id, 0)
                        possible = available / qty_needed
                        can_produce = min(can_produce, possible)
                    # Self-limit based on ticks of supply remaining
                    # If we have less than 50 ticks of inputs, start throttling
                    min_ticks_supply = float('inf')
                    for input_id, qty_needed in commodity.recipe.items():
                        available = station.inventory.get(input_id, 0)
                        ticks_left = available / max(qty_needed * station.effective_rate, 0.001)
                        min_ticks_supply = min(min_ticks_supply, ticks_left)
                    # Throttle factor: 1.0 when 50+ ticks of supply, 0.0 when empty
                    throttle = min(1.0, min_ticks_supply / 50.0)
                    target_rate = min(can_produce, station.production_rate * throttle)
                    station.effective_rate += (target_rate - station.effective_rate) * 0.02
                    station.effective_rate = max(0, min(station.effective_rate, station.production_rate))
                    actual = min(station.effective_rate, can_produce)
                    if actual < 0.01:
                        continue
                    for input_id, qty_needed in commodity.recipe.items():
                        station.inventory[input_id] = station.inventory.get(input_id, 0) - qty_needed * actual
                    station.inventory[commodity_id] = station.inventory.get(commodity_id, 0) + actual

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
                            else:
                                ship.state = "traveling"
                        else:
                            ship.state = "idle"
                    elif ship.state == "unloading":
                        ship.state = "idle"
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
        amount = min(ship.cargo_capacity - sum(ship.cargo.values()), 100 * field.density)
        if amount > 0:
            ship.cargo[commodity] = ship.cargo.get(commodity, 0) + amount
        if sum(ship.cargo.values()) >= ship.cargo_capacity * 0.8:
            ship.state = "idle"
        else:
            ship.state = "mining"
            ship.state_timer = MINING_TICKS

    def _inter_travel_rate(self, from_id: str, to_id: str, speed: float) -> float:
        """Calculate progress per tick based on actual distance. 3-15s per hop."""
        a = self.universe[from_id]
        b = self.universe[to_id]
        dist = math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)
        travel_ticks = max(3, min(15, dist / 70))
        return speed / travel_ticks

    def _move_ships(self):
        for ship in self.ships:
            if ship.state != "traveling" or not ship.destination:
                continue
            rate = self._inter_travel_rate(ship.location, ship.destination, ship.speed)
            ship.progress += rate
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
                else:
                    ship.destination = ""
                    ship.state = "idle"

    def _move_ships_intra(self):
        for ship in self.ships:
            if ship.state != "intra_traveling" or not ship.intra_destination:
                continue
            # Departure delay: negative progress = aligning
            if ship.intra_progress < 0:
                ship.intra_progress += 1  # 1 tick = 1 second countdown
                if ship.intra_progress > 0:
                    ship.intra_progress = 0
                continue
            dist = self._intra_distance(ship.location, ship.intra_position or f"{ship.location}_star", ship.intra_destination)
            # 30-90 ticks to cross based on distance
            travel_ticks = max(30, min(90, dist * 5))
            step = 1.0 / travel_ticks
            ship.intra_progress += step
            if ship.intra_progress >= 1.0:
                ship.intra_position = ship.intra_destination
                ship.intra_destination = ""
                ship.intra_progress = 0.0
                obj = self._get_object(ship.location, ship.intra_position)
                if obj and obj.obj_type == "gate" and ship.destination and obj.connects_to == ship.destination:
                    ship.state = "traveling"
                    ship.progress = 0.0
                else:
                    ship.state = "idle"

    # ── NPC Decisions ────────────────────────────────────────────────────────

    def _npc_decisions(self):
        for ship in self.ships:
            if ship.state != "idle":
                continue
            if ship.role not in ("hauler", "miner", "freelance"):
                continue
            if ship.role == "miner":
                self._miner_decision(ship)
            elif ship.role == "freelance":
                self._freelance_decision(ship)
            else:
                self._trader_decision(ship)

    def _trader_decision(self, ship: NPCShip):
        """Contract hauler: fetch inputs for assigned station from nearest source."""
        loc = self.universe[ship.location]

        # Navigate to a station if not at one
        station_objs = [o for o in loc.objects if o.obj_type == "station"]
        at_station = any(ship.intra_position == o.id for o in station_objs)
        if not at_station and station_objs:
            self._start_intra_travel(ship, station_objs[0].id)
            return

        # If carrying cargo, deliver to assigned station
        if ship.cargo:
            if ship.location == ship.assigned_system:
                target = next((st for st in loc.stations if st.name == ship.assigned_station), None)
                if target:
                    for commodity, qty in list(ship.cargo.items()):
                        target.inventory[commodity] = target.inventory.get(commodity, 0) + qty
                    ship.cargo.clear()
                    ship.state = "unloading"
                    ship.state_timer = UNLOADING_TICKS
                    self.trade_volume += 1
                    return
            # Not home yet, travel there
            self._send_ship(ship, ship.assigned_system)
            return

        # No cargo: figure out what station needs, go get it
        home_sys = self.universe.get(ship.assigned_system)
        if not home_sys:
            return
        target = next((st for st in home_sys.stations if st.name == ship.assigned_station), None)
        if not target:
            return

        # Find input with lowest stock
        needed = None
        lowest = float('inf')
        for prod_id in target.produces:
            c = COMMODITIES.get(prod_id)
            if not c or not c.recipe:
                continue
            for inp_id, qty in c.recipe.items():
                stock = target.inventory.get(inp_id, 0)
                if stock < lowest:
                    lowest = stock
                    needed = inp_id

        if not needed:
            return

        # Find nearest source with stock (search same region only, max 50 systems checked)
        best_src = None
        best_hops = 999
        home_region = getattr(home_sys, 'region', '')
        checked = 0
        for sid, sys in self.universe.items():
            if checked > 50:
                break
            if getattr(sys, 'region', '') != home_region:
                continue
            if self._system_danger(sid) > ship.risk_tolerance:
                continue
            checked += 1
            for st in sys.stations:
                if st.name == ship.assigned_station:
                    continue
                if st.inventory.get(needed, 0) > 100:
                    hops = self._estimate_hops(ship.location, sid)
                    if hops < best_hops:
                        best_hops = hops
                        best_src = (sid, st)

        if best_src:
            src_sys, src_station = best_src
            if ship.location == src_sys:
                # Buy here
                available = src_station.inventory.get(needed, 0)
                buy_qty = min(available * 0.5, ship.cargo_capacity)  # don't drain source
                if buy_qty > 1:
                    src_station.inventory[needed] -= buy_qty
                    ship.cargo[needed] = buy_qty
                    ship.state = "loading"
                    ship.state_timer = LOADING_TICKS
                    ship.route_path = self._find_path(ship.location, ship.assigned_system, ship.risk_tolerance)
                    ship.destination = ship.route_path[0] if ship.route_path else ship.assigned_system
                    return
            else:
                self._send_ship(ship, src_sys)
                return

    def _freelance_decision(self, ship: NPCShip):
        """Freelance trader: find buy-low sell-high opportunities across the region."""
        loc = self.universe[ship.location]

        # Navigate to a station if not at one
        station_objs = [o for o in loc.objects if o.obj_type == "station"]
        at_station = any(ship.intra_position == o.id for o in station_objs)
        if not at_station and station_objs:
            self._start_intra_travel(ship, station_objs[0].id)
            return

        # If carrying cargo, sell at best local station or travel to sell target
        if ship.cargo:
            best_sell = self._find_best_sell(ship, loc)
            if best_sell:
                commodity, station, price = best_sell
                qty = ship.cargo.pop(commodity)
                station.inventory[commodity] = station.inventory.get(commodity, 0) + qty
                ship.state = "unloading"
                ship.state_timer = UNLOADING_TICKS
                self.trade_volume += 1
                return
            # Look for a buyer in region
            for neighbor_id in loc.connections:
                if self._system_danger(neighbor_id) <= ship.risk_tolerance:
                    if self._send_ship(ship, neighbor_id):
                        return
            return

        # No cargo: find a trade opportunity
        best = self._find_best_trade(ship, loc)
        if best:
            commodity, station, dest_id, profit = best
            if ship.location == self.universe[ship.location].id:
                available = station.inventory.get(commodity, 0)
                buy_qty = min(available * 0.3, ship.cargo_capacity)
                if buy_qty > 1:
                    station.inventory[commodity] -= buy_qty
                    ship.cargo[commodity] = buy_qty
                    ship.state = "loading"
                    ship.state_timer = LOADING_TICKS
                    ship.route_path = self._find_path(ship.location, dest_id, ship.risk_tolerance)
                    ship.destination = ship.route_path[0] if ship.route_path else dest_id
                    return
        # Wander to a neighbor
        neighbors = [n for n in loc.connections if self._system_danger(n) <= ship.risk_tolerance]
        if neighbors:
            self._send_ship(ship, random.choice(neighbors))

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
        """Fast distance estimate (Euclidean, no pathfinding)."""
        if from_id == to_id:
            return 0
        a = self.universe.get(from_id)
        b = self.universe.get(to_id)
        if not a or not b:
            return 99
        dist = ((a.x-b.x)**2 + (a.y-b.y)**2 + (a.z-b.z)**2) ** 0.5
        return int(dist / 80) + 1  # ~80 units per hop
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
                    base_price = calculate_price(commodity_id, supply, demand, COMMODITIES)
                    # Apply pressure as percentage modifier
                    new_price = round(base_price * (1 + pressure / 100), 2)
                    old_price = station.price_cache.get(commodity_id, new_price)
                    station.price_cache[commodity_id] = new_price
                    # Log significant price changes (>10%)
                    if old_price > 0 and stock > 1:
                        pct = (new_price - old_price) / old_price * 100
                        if abs(pct) > 10:
                            name = COMMODITIES[commodity_id].name
                            direction = "▲" if pct > 0 else "▼"
                            self._log(f"{direction} {name} {pct:+.0f}% at {station.name} ({sys.name})")

    def _log(self, msg: str):
        self.events.append({"tick": self.tick_count, "time": time.time(), "msg": msg})

    def _generate_faction_events(self):
        """Generate meaningful faction-level events."""
        # Production health by faction
        faction_prod = {}
        faction_halted = {}
        for sid, sys in self.universe.items():
            if not sys.faction:
                continue
            for st in sys.stations:
                for prod_id in st.produces:
                    com = COMMODITIES.get(prod_id)
                    if not com or not com.recipe:
                        continue
                    faction_prod[sys.faction] = faction_prod.get(sys.faction, 0) + 1
                    can = all(st.inventory.get(inp, 0) >= qty for inp, qty in com.recipe.items())
                    if not can:
                        faction_halted[sys.faction] = faction_halted.get(sys.faction, 0) + 1

        fnames = {'terran_fed': 'Federation', 'science_collective': 'Nexus', 'merchants_guild': 'Guild', 'free_states': 'Alliance', 'iron_compact': 'Compact'}
        for fid, total in faction_prod.items():
            halted = faction_halted.get(fid, 0)
            fname = fnames.get(fid, fid)
            if halted > total * 0.5:
                self._log(f"ECONOMY: {fname} production crisis - {halted}/{total} lines halted")
            elif halted == 0:
                self._log(f"ECONOMY: {fname} all production lines operational")

        # Trade activity
        if self.trade_volume > 0:
            self._log(f"TRADE: {self.trade_volume} deliveries completed this cycle")

        # Fleet strength
        status = self.warfare.get_status()
        for fid, strength in status.get('fleet_strength', {}).items():
            fname = fnames.get(fid, fid)
            if strength < 10:
                self._log(f"MILITARY: {fname} fleet critically low ({strength} ships)")

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
