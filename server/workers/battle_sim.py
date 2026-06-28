"""Battle Simulation worker: processes faction fleet combat."""
import random
from server.supervisor import WorkerThread
from server.intents import ShipDestroyedEvent, ShipBuiltEvent, EventLog
from server.data_access import load_military_ships, load_fleet_targets, load_factions

MILITARY_SHIPS = load_military_ships()
FLEET_TARGETS = load_fleet_targets()
_factions_data = load_factions()
FACTIONS = {k: v['name'] for k, v in _factions_data.items()}
FACTION_SHORTS = {k: v['short'] for k, v in _factions_data.items()}


class BattleSimWorker(WorkerThread):
    def __init__(self):
        super().__init__("battle_sim", tick_interval=20)
        self.fleets = {}
        for faction_id, targets in FLEET_TARGETS.items():
            self.fleets[faction_id] = dict(targets)
        self.conflicts = [
            ("iron_compact", "free_states"),
            ("corsairs", "merchants_guild"),
            ("corsairs", "terran_fed"),
            ("corsairs", "science_collective"),
        ]
        # Shipyard build queues: {station_name: [{ship_class_id, faction_id, ticks_remaining, cost_consumed}]}
        self._build_queues = {}
        self._max_slipways = {'shipyard': 4}  # slots per shipyard
        # Cache build times (seconds -> ticks at 360s/tick)
        self._build_ticks = {}
        import sqlite3, os
        _db = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "game_data.db")
        try:
            _c = sqlite3.connect(_db)
            for row in _c.execute("SELECT id, build_time FROM ships WHERE build_time > 0"):
                self._build_ticks[row[0]] = max(1, row[1] // 360)
            _c.close()
        except:
            pass

    def process(self, tick: int, snapshot):
        universe = snapshot['universe']

        # Run skirmishes
        for attacker_id, defender_id in self.conflicts:
            if random.random() < 0.3:
                self._run_skirmish(attacker_id, defender_id, tick)

        # Progress build queues every tick (this worker runs every 20 ticks, so advance 20)
        self._progress_builds(universe, tick, 20)

        # Queue new builds if slots available
        if tick % 20 == 0:
            self._queue_builds(universe, tick)

    def _progress_builds(self, universe, tick, dt):
        """Advance all active build timers. Complete ships when timer reaches 0."""
        for station_name, queue in list(self._build_queues.items()):
            for build in list(queue):
                build['ticks_remaining'] -= dt
                if build['ticks_remaining'] <= 0:
                    # Ship complete!
                    queue.remove(build)
                    faction_id = build['faction_id']
                    ship_class_id = build['ship_class_id']
                    current = self.fleets.get(faction_id, {})
                    current[ship_class_id] = current.get(ship_class_id, 0) + 1
                    ship = MILITARY_SHIPS[ship_class_id]
                    # Find the system for this station
                    sys_id = build.get('system_id', '')
                    self.emit(ShipBuiltEvent(
                        faction_id=faction_id, ship_class_id=ship_class_id,
                        system_id=sys_id, station_name=station_name,
                        cost={},  # already consumed when queued
                        fitting_cost=dict(ship.fitting_cost) if ship.fitting_cost else None
                    ))
                    short = FACTION_SHORTS.get(faction_id, faction_id)
                    self.emit(EventLog(tick=tick, msg=f"BUILT: {ship.name} for {short} at {station_name}"))

    def _queue_builds(self, universe, tick):
        """Try to queue new ship builds at shipyards with available slots."""
        for faction_id, targets in FLEET_TARGETS.items():
            current = self.fleets.get(faction_id, {})
            for ship_class_id, target_count in targets.items():
                deficit = target_count - current.get(ship_class_id, 0)
                if deficit <= 0:
                    continue
                # Already building this type?
                already_building = sum(
                    1 for q in self._build_queues.values()
                    for b in q if b['ship_class_id'] == ship_class_id and b['faction_id'] == faction_id
                )
                if already_building >= deficit:
                    continue

                ship = MILITARY_SHIPS[ship_class_id]
                queued = False
                for sys in universe.values():
                    if queued:
                        break
                    if sys.faction != faction_id:
                        continue
                    for station in sys.stations:
                        if station.station_type != "shipyard":
                            continue
                        # Check slot availability
                        queue = self._build_queues.setdefault(station.name, [])
                        if len(queue) >= self._max_slipways.get('shipyard', 4):
                            continue
                        # Check if materials available
                        can_build = all(
                            station.inventory.get(cid, 0) >= qty
                            for cid, qty in ship.build_cost.items()
                        )
                        if not can_build:
                            continue
                        # Consume materials and start build
                        for cid, qty in ship.build_cost.items():
                            station.inventory[cid] = max(0, station.inventory.get(cid, 0) - qty)
                        build_ticks = self._build_ticks.get(ship_class_id, 4)  # default 4 ticks for fighters

                        queue.append({
                            'ship_class_id': ship_class_id,
                            'faction_id': faction_id,
                            'ticks_remaining': build_ticks,
                            'system_id': sys.id,
                        })
                        short = FACTION_SHORTS.get(faction_id, faction_id)
                        self.emit(EventLog(tick=tick, msg=f"QUEUE: {ship.name} at {station.name} ({build_ticks} ticks)"))
                        queued = True
                        break

    def _run_skirmish(self, attacker_id: str, defender_id: str, tick: int):
        a_fleet = self.fleets.get(attacker_id, {})
        d_fleet = self.fleets.get(defender_id, {})
        if not any(v > 0 for v in a_fleet.values()) or not any(v > 0 for v in d_fleet.values()):
            return

        a_losses = 0
        d_losses = 0

        for _ in range(random.randint(1, 2)):
            available = [(k, v) for k, v in a_fleet.items() if v > 0]
            if available:
                weights = [v * (3 if MILITARY_SHIPS[k].hull_class in ('fighter', 'frigate') else 1) for k, v in available]
                chosen = random.choices(available, weights=weights, k=1)[0]
                a_fleet[chosen[0]] -= 1
                a_losses += 1
                self.emit(ShipDestroyedEvent(faction_id=attacker_id, ship_class_id=chosen[0]))

        for _ in range(random.randint(1, 2)):
            available = [(k, v) for k, v in d_fleet.items() if v > 0]
            if available:
                weights = [v * (3 if MILITARY_SHIPS[k].hull_class in ('fighter', 'frigate') else 1) for k, v in available]
                chosen = random.choices(available, weights=weights, k=1)[0]
                d_fleet[chosen[0]] -= 1
                d_losses += 1
                self.emit(ShipDestroyedEvent(faction_id=defender_id, ship_class_id=chosen[0]))

        a_name = FACTIONS.get(attacker_id, attacker_id)
        d_name = FACTIONS.get(defender_id, defender_id)
        self.emit(EventLog(tick=tick, msg=f"BATTLE: {a_name} vs {d_name} ({a_losses}+{d_losses} ships lost)"))

    def get_status(self) -> dict:
        building = sum(len(q) for q in self._build_queues.values())
        return {
            "fleet_strength": {fid: sum(f.values()) for fid, f in self.fleets.items()},
            "ships_building": building,
        }
