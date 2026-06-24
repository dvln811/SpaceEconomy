"""Supervisor: owns the tick clock, coordinates worker threads, merges intents."""
import threading
import time
import logging
from queue import Queue, Empty

from server.intents import (
    InventoryDelta, ShipMoveIntent, ShipIntraIntent, ShipBuyIntent,
    ShipSellIntent, ShipMineIntent, ShipDestroyedEvent, ShipBuiltEvent,
    SpawnCommand, FactionOrder, PriceUpdate, EventLog,
)
from server.change_tracker import ChangeTracker

log = logging.getLogger("supervisor")

LOADING_TICKS = 3
UNLOADING_TICKS = 2
MINING_TICKS = 5


class WorkerThread:
    """Base wrapper for a simulation worker running in its own thread."""

    def __init__(self, name: str, tick_interval: int = 1):
        self.name = name
        self.tick_interval = tick_interval  # run every N ticks
        self.intent_queue = Queue()
        self._event = threading.Event()
        self._done_event = threading.Event()
        self._stop = False
        self._thread = None
        self._tick_count = 0
        self._snapshot = None

    def start(self):
        self._thread = threading.Thread(target=self._loop, name=self.name, daemon=True)
        self._thread.start()

    def signal_tick(self, tick_count: int, snapshot):
        """Supervisor signals this worker to process a tick."""
        self._tick_count = tick_count
        self._snapshot = snapshot
        self._done_event.clear()
        self._event.set()

    def wait_done(self, timeout: float = 2.0) -> bool:
        """Wait for worker to finish current tick processing."""
        return self._done_event.wait(timeout=timeout)

    def stop(self):
        self._stop = True
        self._event.set()

    def _loop(self):
        while not self._stop:
            self._event.wait()
            self._event.clear()
            if self._stop:
                break
            if self._tick_count % self.tick_interval == 0:
                try:
                    self.process(self._tick_count, self._snapshot)
                except Exception as e:
                    log.error(f"Worker {self.name} error: {e}", exc_info=True)
            self._done_event.set()

    def process(self, tick: int, snapshot):
        """Override in subclass. Produce intents via self.emit(intent)."""
        raise NotImplementedError

    def emit(self, intent):
        self.intent_queue.put(intent)

    def drain_intents(self) -> list:
        """Drain all pending intents from queue."""
        intents = []
        while True:
            try:
                intents.append(self.intent_queue.get_nowait())
            except Empty:
                break
        return intents


class Supervisor:
    """Tick clock + intent merger. Replaces the old economy_loop."""

    def __init__(self, sim):
        self.sim = sim
        self.workers: list[WorkerThread] = []
        self.tick_rate = 1.0  # seconds between ticks
        self.multiplier = 1
        self._stop = False
        self._thread = None
        self.change_tracker = ChangeTracker()
        # Build region cache and ship index for workers
        self._region_cache = {}  # {region: {commodity: [(system_id, station_name, qty)]}}
        self._ship_index = {}  # {ship_id: ship}
        self._station_index = {}  # {(system_id, station_name): station}
        self._rebuild_indices()
        # Performance metrics
        self.metrics = {
            'ticks_per_sec': 0.0,
            'tick_ms': 0.0,
            'movement_ms': 0.0,
            'workers_ms': 0.0,
            'merge_ms': 0.0,
            'worker_times': {},  # {name: ms}
            'intents_per_tick': 0,
        }
        self._tick_times = []  # last 10 tick timestamps for ticks/sec calc

    def add_worker(self, worker: WorkerThread):
        self.workers.append(worker)

    def start(self):
        for w in self.workers:
            w.start()
        self._thread = threading.Thread(target=self._tick_loop, name="supervisor", daemon=True)
        self._thread.start()
        log.info(f"Supervisor started with {len(self.workers)} workers")

    def stop(self):
        self._stop = True
        for w in self.workers:
            w.stop()

    def _tick_loop(self):
        from server.persistence import save_simulation
        while not self._stop:
            t0 = time.time()
            for _ in range(self.multiplier):
                self._do_tick()
            if self.sim.tick_count % 10 == 0:
                save_simulation(self.sim)
            elapsed = time.time() - t0
            sleep_time = max(0, self.tick_rate - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _do_tick(self):
        self.sim.tick_count += 1
        tick = self.sim.tick_count
        t_start = time.time()

        # Movement (stays in supervisor, fast and needs direct state mutation)
        self._process_timers()
        self._move_ships()
        self._move_ships_intra()
        t_move = time.time()

        # Build snapshot for workers
        snapshot = {
            'tick': tick,
            'universe': self.sim.universe,
            'ships': self.sim.ships,
            'region_cache': self._region_cache,
            'ship_index': self._ship_index,
        }

        # Signal all workers
        for w in self.workers:
            w.signal_tick(tick, snapshot)

        # Wait for completion (with timeout to avoid deadlock)
        worker_times = {}
        for w in self.workers:
            wt0 = time.time()
            if not w.wait_done(timeout=5.0):
                log.warning(f"Worker {w.name} timed out on tick {tick}")
            worker_times[w.name] = (time.time() - wt0) * 1000
        t_workers = time.time()

        # Collect and apply intents
        intent_count = 0
        changed_systems = set()
        for w in self.workers:
            for intent in w.drain_intents():
                self._apply_intent_fast(intent, tick, changed_systems)
                intent_count += 1
        # Batch record system changes
        for sid in changed_systems:
            self.change_tracker.record_system_change(tick, sid)
        t_merge = time.time()

        # Rebuild indices periodically
        if tick % 10 == 0:
            self._rebuild_indices()

        # Update metrics
        now = time.time()
        self._tick_times.append(now)
        if len(self._tick_times) > 10:
            self._tick_times = self._tick_times[-10:]
        if len(self._tick_times) >= 2:
            span = self._tick_times[-1] - self._tick_times[0]
            self.metrics['ticks_per_sec'] = round((len(self._tick_times) - 1) / span, 2) if span > 0 else 0
        self.metrics['tick_ms'] = round((now - t_start) * 1000, 1)
        self.metrics['movement_ms'] = round((t_move - t_start) * 1000, 1)
        self.metrics['workers_ms'] = round((t_workers - t_move) * 1000, 1)
        self.metrics['merge_ms'] = round((t_merge - t_workers) * 1000, 1)
        self.metrics['worker_times'] = {k: round(v, 1) for k, v in worker_times.items()}
        self.metrics['intents_per_tick'] = intent_count

        # Trim events
        if len(self.sim.events) > 100:
            self.sim.events = self.sim.events[-100:]

        # Prune old change tracking entries
        self.change_tracker.tick_cleanup(tick)

    def _apply_intent(self, intent, tick: int):
        """Apply a single intent to canonical state (legacy, used by nothing now)."""
        pass

    def _apply_intent_fast(self, intent, tick: int, changed_systems: set):
        """Apply a single intent, batch change tracking into changed_systems set."""
        if isinstance(intent, InventoryDelta):
            sys = self.sim.universe.get(intent.system_id)
            if sys:
                # Use station index if available
                st = self._station_index.get((intent.system_id, intent.station_name))
                if st:
                    for commodity, delta in intent.deltas.items():
                        st.inventory[commodity] = max(0, st.inventory.get(commodity, 0) + delta)
                    changed_systems.add(intent.system_id)

        elif isinstance(intent, PriceUpdate):
            st = self._station_index.get((intent.system_id, intent.station_name))
            if st:
                st.price_cache[intent.commodity_id] = intent.new_price
                changed_systems.add(intent.system_id)

        elif isinstance(intent, ShipMoveIntent):
            ship = self._ship_index.get(intent.ship_id)
            if ship and ship.state == "idle":
                path = intent.route_path or self._find_path(ship.location, intent.destination, ship.risk_tolerance)
                if path:
                    ship.route_path = path
                    ship.destination = path[0]
                    gate_id = self._get_gate_for(ship.location, path[0])
                    if gate_id and ship.intra_position != gate_id:
                        self._start_intra_travel(ship, gate_id)
                    else:
                        ship.state = "traveling"
                        ship.progress = 0.0
                    self.change_tracker.record_ship_change(tick, ship.id)

        elif isinstance(intent, ShipIntraIntent):
            ship = self._ship_index.get(intent.ship_id)
            if ship and ship.state == "idle":
                self._start_intra_travel(ship, intent.dest_obj_id)
                self.change_tracker.record_ship_change(tick, ship.id)

        elif isinstance(intent, ShipBuyIntent):
            ship = self._ship_index.get(intent.ship_id)
            if not ship:
                return
            sys = self.sim.universe.get(intent.system_id)
            if not sys:
                return
            station = next((st for st in sys.stations if st.name == intent.station_name), None)
            if not station:
                return
            available = station.inventory.get(intent.commodity_id, 0)
            buy_qty = min(intent.quantity, available * 0.5, ship.cargo_capacity - sum(ship.cargo.values()))
            if buy_qty > 1:
                station.inventory[intent.commodity_id] -= buy_qty
                ship.cargo[intent.commodity_id] = ship.cargo.get(intent.commodity_id, 0) + buy_qty
                ship.state = "loading"
                ship.state_timer = LOADING_TICKS
                ship.route_path = intent.route_home
                ship.destination = intent.route_home[0] if intent.route_home else ship.assigned_system
                self.change_tracker.record_ship_change(tick, ship.id)
                changed_systems.add(intent.system_id)

        elif isinstance(intent, ShipSellIntent):
            ship = self._ship_index.get(intent.ship_id)
            if not ship:
                return
            sys = self.sim.universe.get(intent.system_id)
            if not sys:
                return
            station = next((st for st in sys.stations if st.name == intent.station_name), None)
            if not station:
                return
            qty = ship.cargo.pop(intent.commodity_id, 0)
            if qty > 0:
                station.inventory[intent.commodity_id] = station.inventory.get(intent.commodity_id, 0) + qty
                ship.state = "unloading"
                ship.state_timer = UNLOADING_TICKS
                self.sim.trade_volume += 1
                self.change_tracker.record_ship_change(tick, ship.id)
                changed_systems.add(intent.system_id)

        elif isinstance(intent, ShipMineIntent):
            ship = self._ship_index.get(intent.ship_id)
            if ship and ship.state == "idle":
                ship.state = "mining"
                ship.state_timer = MINING_TICKS
                self.change_tracker.record_ship_change(tick, ship.id)

        elif isinstance(intent, ShipDestroyedEvent):
            if hasattr(self.sim, 'warfare'):
                fleet = self.sim.warfare.fleets.get(intent.faction_id, {})
                if fleet.get(intent.ship_class_id, 0) > 0:
                    fleet[intent.ship_class_id] -= 1
                    self.sim.warfare.ships_destroyed += 1

        elif isinstance(intent, ShipBuiltEvent):
            if hasattr(self.sim, 'warfare'):
                fleet = self.sim.warfare.fleets.get(intent.faction_id, {})
                fleet[intent.ship_class_id] = fleet.get(intent.ship_class_id, 0) + 1
                self.sim.warfare.ships_built += 1
            # Consume materials
            sys = self.sim.universe.get(intent.system_id)
            if sys:
                station = next((st for st in sys.stations if st.name == intent.station_name), None)
                if station:
                    for commodity, qty in intent.cost.items():
                        station.inventory[commodity] = max(0, station.inventory.get(commodity, 0) - qty)

        elif isinstance(intent, SpawnCommand):
            # Spawning handled by Corsair worker results; actual spawn logic TBD
            pass

        elif isinstance(intent, FactionOrder):
            # Faction strategy results; actual application TBD
            pass

        elif isinstance(intent, EventLog):
            self.sim.events.append({"tick": intent.tick, "time": time.time(), "msg": intent.msg})

    def _rebuild_indices(self):
        """Rebuild region inventory cache, ship index, and station index."""
        self._ship_index = {s.id: s for s in self.sim.ships}
        # Station index: {(system_id, station_name): station_obj}
        self._station_index = {}
        for sid, sys in self.sim.universe.items():
            for st in sys.stations:
                self._station_index[(sid, st.name)] = st
        # Region cache: {region: {commodity: [(system_id, station_name, qty)]}}
        cache = {}
        for sid, sys in self.sim.universe.items():
            region = sys.region
            if not region:
                continue
            if region not in cache:
                cache[region] = {}
            for st in sys.stations:
                for commodity, qty in st.inventory.items():
                    if qty > 10:
                        if commodity not in cache[region]:
                            cache[region][commodity] = []
                        cache[region][commodity].append((sid, st.name, qty))
        # Sort each commodity list by qty descending
        for region in cache.values():
            for commodity in region:
                region[commodity].sort(key=lambda x: -x[2])
        self._region_cache = cache

    # ── Movement logic (kept in supervisor, fast O(ships) loops) ──

    def _process_timers(self):
        import random
        from server.simulation import COMMODITIES
        tick = self.sim.tick_count
        for ship in self.sim.ships:
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
                        self._complete_mining(ship, random)
                    self.change_tracker.record_ship_change(tick, ship.id)

    def _complete_mining(self, ship, random):
        import random as rnd
        loc = self.sim.universe[ship.location]
        if not loc.asteroid_fields:
            ship.state = "idle"
            return
        field = rnd.choice(loc.asteroid_fields)
        if not field.yields:
            ship.state = "idle"
            return
        commodity = rnd.choice(field.yields)
        amount = min(ship.cargo_capacity - sum(ship.cargo.values()), 100 * field.density)
        if amount > 0:
            ship.cargo[commodity] = ship.cargo.get(commodity, 0) + amount
        if sum(ship.cargo.values()) >= ship.cargo_capacity * 0.8:
            ship.state = "idle"
        else:
            ship.state = "mining"
            ship.state_timer = MINING_TICKS

    def _move_ships(self):
        import math
        tick = self.sim.tick_count
        for ship in self.sim.ships:
            if ship.state != "traveling" or not ship.destination:
                continue
            a = self.sim.universe[ship.location]
            b = self.sim.universe.get(ship.destination)
            if not b:
                ship.state = "idle"
                self.change_tracker.record_ship_change(tick, ship.id)
                continue
            dist = math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)
            travel_ticks = max(3, min(15, dist / 70))
            rate = ship.speed / travel_ticks
            ship.progress += rate
            if ship.progress >= 1.0:
                ship.progress = 0.0
                ship.location = ship.destination
                arrival_gate = ""
                for o in self.sim.universe[ship.location].objects:
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
                self.change_tracker.record_ship_change(tick, ship.id)

    def _move_ships_intra(self):
        import math
        tick = self.sim.tick_count
        for ship in self.sim.ships:
            if ship.state != "intra_traveling" or not ship.intra_destination:
                continue
            if ship.intra_progress < 0:
                ship.intra_progress += 1
                if ship.intra_progress > 0:
                    ship.intra_progress = 0
                continue
            dist = self._intra_distance(ship.location, ship.intra_position or f"{ship.location}_star", ship.intra_destination)
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
                self.change_tracker.record_ship_change(tick, ship.id)

    def _start_intra_travel(self, ship, dest_obj_id: str):
        if ship.intra_position == dest_obj_id:
            return
        ship.intra_destination = dest_obj_id
        ship.intra_progress = -ship.align_time
        ship.state = "intra_traveling"

    def _get_gate_for(self, system_id: str, dest_system_id: str) -> str:
        for o in self.sim.universe[system_id].objects:
            if o.obj_type == "gate" and o.connects_to == dest_system_id:
                return o.id
        return ""

    def _get_object(self, system_id: str, obj_id: str):
        for o in self.sim.universe[system_id].objects:
            if o.id == obj_id:
                return o
        return None

    def _intra_distance(self, system_id: str, obj_a_id: str, obj_b_id: str) -> float:
        import math
        a = self._get_object(system_id, obj_a_id)
        b = self._get_object(system_id, obj_b_id)
        if not a or not b:
            return 1.0
        ax = a.distance * math.cos(a.angle)
        ay = a.distance * math.sin(a.angle)
        bx = b.distance * math.cos(b.angle)
        by = b.distance * math.sin(b.angle)
        return max(0.5, math.sqrt((ax - bx)**2 + (ay - by)**2))

    def _find_path(self, from_id: str, to_id: str, risk_tolerance: float = 1.0) -> list[str]:
        from server.models import SECURITY_LEVEL
        if from_id == to_id:
            return []
        visited = {from_id}
        queue = [(from_id, [])]
        while queue:
            current, path = queue.pop(0)
            for neighbor in self.sim.universe[current].connections:
                if neighbor in visited:
                    continue
                danger = 1.0 - SECURITY_LEVEL.get(self.sim.universe[neighbor].security, 0.0)
                if neighbor != to_id and danger > risk_tolerance:
                    continue
                new_path = path + [neighbor]
                if neighbor == to_id:
                    return new_path
                visited.add(neighbor)
                queue.append((neighbor, new_path))
        return []
