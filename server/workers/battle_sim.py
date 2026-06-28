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
        # Track fleet state locally (supervisor also updates via intents)
        self.fleets = {}
        for faction_id, targets in FLEET_TARGETS.items():
            self.fleets[faction_id] = dict(targets)
        self.conflicts = [
            ("iron_compact", "free_states"),
            ("corsairs", "merchants_guild"),
            ("corsairs", "terran_fed"),
            ("corsairs", "science_collective"),
        ]

    def process(self, tick: int, snapshot):
        universe = snapshot['universe']

        # Run skirmishes every 20 ticks - moderate probability
        for attacker_id, defender_id in self.conflicts:
            if random.random() < 0.3:
                self._run_skirmish(attacker_id, defender_id, tick)

        # Try to build replacement ships every 10 ticks (faster rebuild)
        if tick % 10 == 0:
            self._try_build(universe, tick)

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

    def _try_build(self, universe, tick: int):
        for faction_id, targets in FLEET_TARGETS.items():
            current = self.fleets.get(faction_id, {})
            for ship_class_id, target_count in targets.items():
                deficit = target_count - current.get(ship_class_id, 0)
                if deficit <= 0:
                    continue
                ship = MILITARY_SHIPS[ship_class_id]
                for sys in universe.values():
                    if sys.faction != faction_id:
                        continue
                    for station in sys.stations:
                        if station.station_type != "shipyard":
                            continue
                        can_build = all(
                            station.inventory.get(cid, 0) >= qty
                            for cid, qty in ship.build_cost.items()
                        )
                        if can_build:
                            current[ship_class_id] = current.get(ship_class_id, 0) + 1
                            self.emit(ShipBuiltEvent(
                                faction_id=faction_id, ship_class_id=ship_class_id,
                                system_id=sys.id, station_name=station.name,
                                cost=dict(ship.build_cost),
                                fitting_cost=dict(ship.fitting_cost) if hasattr(ship, 'fitting_cost') and ship.fitting_cost else None
                            ))
                            short = FACTION_SHORTS.get(faction_id, faction_id)
                            self.emit(EventLog(tick=tick, msg=f"BUILT: {ship.name} for {short} at {station.name}"))
                            break
                    if current.get(ship_class_id, 0) >= target_count:
                        break

    def get_status(self) -> dict:
        return {
            "fleet_strength": {fid: sum(f.values()) for fid, f in self.fleets.items()},
        }
